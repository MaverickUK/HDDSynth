"""
ISA Bus Monitoring Module for HDDSynth
Handles PIO-based and fallback pin monitoring of ISA bus activity.
"""

import time
import board
import digitalio

# Try to import PIO support
try:
    import rp2
    PIO_AVAILABLE = True
except ImportError:
    PIO_AVAILABLE = False

class ISAMonitor:
    """Monitors ISA bus for HDD activity using PIO or fallback pin monitoring."""
    
    def __init__(self, config):
        """Initialize ISA monitor with configuration."""
        self.config = config
        self.addr_pins = []
        self.ior_pin = None
        self.iow_pin = None
        self.sm_ior = None
        self.sm_iow = None
        
        # Activity tracking
        self.hdd_activity_counter = 0
        self.hdd_poll_counter = 0
        self.last_activity_time = time.monotonic()
        
        # State tracking for fallback mode
        self.prev_ior_state = None
        self.prev_iow_state = None
        
        # Initialize pins and monitoring
        self._init_pins()
        self._init_monitoring()
    
    def _init_pins(self):
        """Initialize address and control pins."""
        # Configure address pins as inputs with pull-up resistors
        for i in range(self.config.ADDR_PIN_COUNT):
            pin = digitalio.DigitalInOut(getattr(board, f"GP{self.config.ADDR_PIN_BASE + i}"))
            pin.pull = digitalio.Pull.UP
            self.addr_pins.append(pin)
        
        # Configure control pins (IOR/IOW) as inputs with pull-up resistors
        self.ior_pin = digitalio.DigitalInOut(getattr(board, f"GP{self.config.IOR_PIN}"))
        self.ior_pin.pull = digitalio.Pull.UP
        
        self.iow_pin = digitalio.DigitalInOut(getattr(board, f"GP{self.config.IOW_PIN}"))
        self.iow_pin.pull = digitalio.Pull.UP
        
        # Store initial states for fallback mode
        self.prev_ior_state = self.ior_pin.value
        self.prev_iow_state = self.iow_pin.value
    
    def _init_monitoring(self):
        """Initialize PIO monitoring or fallback to simple pin monitoring."""
        if PIO_AVAILABLE:
            try:
                self._init_pio_monitoring()
                print("✅ PIO-based ISA monitoring initialized")
            except Exception as e:
                print(f"⚠️  PIO initialization failed: {e}")
                PIO_AVAILABLE = False
        
        if not PIO_AVAILABLE:
            print("ℹ️  Using fallback pin monitoring")
    
    def _init_pio_monitoring(self):
        """Initialize PIO state machines for high-speed monitoring."""
        # PIO program for IOR monitoring
        @rp2.asm_pio(
            in_shiftdir=rp2.PIO.SHIFT_LEFT,
            autopush=True,
            push_thresh=10,
            fifo_join=rp2.PIO.JOIN_RX
        )
        def ior_pio_program():
            wrap_target()
            wait(0, pin, 0)  # Wait for IOR pin to go low
            in_(pins, 10)     # Read 10 address pins
            wrap()
        
        # PIO program for IOW monitoring
        @rp2.asm_pio(
            in_shiftdir=rp2.PIO.SHIFT_LEFT,
            autopush=True,
            push_thresh=10,
            fifo_join=rp2.PIO.JOIN_RX
        )
        def iow_pio_program():
            wrap_target()
            wait(0, pin, 0)  # Wait for IOW pin to go low
            in_(pins, 10)     # Read 10 address pins
            wrap()
        
        # Create and configure state machines
        self.sm_ior = rp2.StateMachine(
            0,
            ior_pio_program,
            freq=self.config.ISA_BUS_FREQ,
            in_base=getattr(board, f"GP{self.config.ADDR_PIN_BASE}"),
            jmp_pin=self.ior_pin
        )
        
        self.sm_iow = rp2.StateMachine(
            1,
            iow_pio_program,
            freq=self.config.ISA_BUS_FREQ,
            in_base=getattr(board, f"GP{self.config.ADDR_PIN_BASE}"),
            jmp_pin=self.iow_pin
        )
        
        # Start state machines
        self.sm_ior.active(True)
        self.sm_iow.active(True)
    
    def _read_address_bus(self):
        """Read the current state of the address bus."""
        addr = 0
        for i, pin in enumerate(self.addr_pins):
            if pin.value:
                addr |= (1 << i)
        return addr
    
    def _detect_activity_pio(self):
        """Detect HDD activity using PIO state machines."""
        current_time = time.monotonic()
        activity_detected = False
        
        # Check IOR state machine FIFO
        if self.sm_ior.rx_fifo() > 0:
            addr = self.sm_ior.get()
            self._process_address(addr, current_time)
            activity_detected = True
        
        # Check IOW state machine FIFO
        if self.sm_iow.rx_fifo() > 0:
            addr = self.sm_iow.get()
            self._process_address(addr, current_time)
            activity_detected = True
        
        return activity_detected
    
    def _detect_activity_fallback(self):
        """Detect HDD activity using simple pin monitoring."""
        current_time = time.monotonic()
        activity_detected = False
        
        # Check IOR activity (falling edge detection)
        current_ior_state = self.ior_pin.value
        if current_ior_state != self.prev_ior_state and current_ior_state == False:
            addr = self._read_address_bus()
            self._process_address(addr, current_time)
            activity_detected = True
        self.prev_ior_state = current_ior_state
        
        # Check IOW activity (falling edge detection)
        current_iow_state = self.iow_pin.value
        if current_iow_state != self.prev_iow_state and current_iow_state == False:
            addr = self._read_address_bus()
            self._process_address(addr, current_time)
            activity_detected = True
        self.prev_iow_state = current_iow_state
        
        return activity_detected
    
    def _process_address(self, addr, current_time):
        """Process detected address and update activity counters."""
        self.last_activity_time = current_time
        
        if addr == self.config.HDD_DATA_PORT:
            self.hdd_activity_counter += 1
            if self.config.VERBOSE_ACTIVITY_LOGGING:
                print(f"HDD Data: 0x{addr:03X} (count: {self.hdd_activity_counter})")
        elif addr == self.config.HDD_STATUS_PORT:
            self.hdd_poll_counter += 1
            if self.config.VERBOSE_ACTIVITY_LOGGING:
                print(f"HDD Status: 0x{addr:03X} (count: {self.hdd_poll_counter})")
    
    def _reset_counters_if_timeout(self):
        """Reset activity counters if timeout exceeded."""
        current_time = time.monotonic()
        timeout_seconds = self.config.ACTIVITY_TIMEOUT_MS / 1000.0
        
        if (current_time - self.last_activity_time) > timeout_seconds:
            if self.hdd_activity_counter > 0 or self.hdd_poll_counter > 0:
                print(" | ", end="")  # Activity separator
            self.hdd_activity_counter = 0
            self.hdd_poll_counter = 0
    
    def detect_hdd_activity(self):
        """Detect HDD activity and return activity state."""
        # Reset counters if timeout exceeded
        self._reset_counters_if_timeout()
        
        # Detect activity using appropriate method
        if PIO_AVAILABLE and self.sm_ior and self.sm_iow:
            self._detect_activity_pio()
        else:
            self._detect_activity_fallback()
        
        # Check if activity threshold exceeded
        hdd_active = self.hdd_activity_counter > self.config.ACTIVITY_THRESHOLD
        hdd_polling = self.hdd_poll_counter > self.config.ACTIVITY_THRESHOLD
        
        # Reset counters if threshold exceeded
        if hdd_active:
            self.hdd_activity_counter = 0
        if hdd_polling:
            self.hdd_poll_counter = 0
        
        return hdd_active or hdd_polling
    
    def cleanup(self):
        """Clean up resources."""
        # Stop PIO state machines if they exist
        if self.sm_ior:
            self.sm_ior.active(False)
        if self.sm_iow:
            self.sm_iow.active(False)
        
        # Clean up pins
        for pin in self.addr_pins:
            pin.deinit()
        if self.ior_pin:
            self.ior_pin.deinit()
        if self.iow_pin:
            self.iow_pin.deinit()
