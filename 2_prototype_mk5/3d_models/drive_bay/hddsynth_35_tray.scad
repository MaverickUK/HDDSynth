// ============================================================
//  HDD Synth MKV  ->  3.5" drive bay adapter tray   [rev B]
//  Target: SFF-8301 (3.5") / SFF-8201 (2.5" hole pattern)
//
//  Rev B changes:
//   - M3 pilots opened to 2.8mm (self-tap in plastic, no drilling)
//   - Slot venting extended across the whole base plate
//   - Recessed pocket for the HDD Synth logo label
//   - Optional Pimoroni 4ohm 3W speaker mount (COM1602)
//
//  Orientation: y=0 REAR (USB-C end, left open), y=bay_l FRONT.
//               z=0 is the bottom datum plane.
//  Print flat, no supports.
// ============================================================

use <hddsynth_logo.scad>

$fn = 48;

show_pcb = false;      // ghost the board in F5 preview

// ---- 3.5" bay envelope, SFF-8301 --------------------------
bay_w     = 101.60;    // A3
bay_l     = 146.00;    // A2 (147.00 max)
bay_h_max =  26.10;    // A1 - reference only

bot_span  =  95.25;    // A4
bot_y     = [41.28, 85.73, 117.48];   // A7, A7+A6, A7+A13
side_z    =   6.35;    // A10
side_y    = [28.50, 130.10];          // A8, A8+A9

bay_pilot =   2.90;    // 6-32 self-tap -> 3.40 for tool-less pins
bay_depth =   5.00;

// ---- HDD Synth MKV board ----------------------------------
pcb_w          =  69.85;
pcb_l          = 100.33;
pcb_t          =   1.60;
pcb_hole_dx    =  61.72;
pcb_hole_rear  =  13.97;
pcb_hole_pitch =  76.60;
pcb_y_offset   =   0.00;   // >0 pushes the board forward

// ---- Tray construction ------------------------------------
base_t  =  3.0;
rail_t  =  5.0;
rail_h  = 12.0;
front_t =  3.0;        // trimmed from 4.0 to make room for the speaker
boss_h  =  3.0;
boss_d  =  7.0;

// PCB fixings - M3
use_inserts  = false;
boss_pilot   = 2.80;   // self-tapping M3 in PETG/PLA - no drilling needed
boss_depth   = 5.00;
insert_d     = 4.00;
insert_depth = 5.50;

// ---- Venting ----------------------------------------------
vent_w     =  9.0;     // slot width
vent_x     = 39.0;     // transverse slot end-centres (+-)
vent_pitch = 11.5;     // ~2.5mm ribs between slots
vent_y0    =  9.0;
vent_y1    = 139.0;
out_seg    = [];       // outboard slots no longer needed - rows now span the full width
out_x      = 36.0;

// ---- Logo ---------------------------------------------------
// Geometry is traced from HDDSynthLogoSmall.png and lives in
// hddsynth_logo.scad - keep that file beside this one.
logo_style  = "engrave";  // "engrave" (cut logo) | "panel" (plain pocket) | "none"
logo_face   = "both";     // "bottom" | "top" | "both"
logo_w      = 50.0;       // artwork is 1.407:1
logo_h      = 35.5;       // = logo_w / 1.407
logo_depth  =  0.6;       // per face; 2x0.6 in a 3mm plate leaves a 1.8mm web
logo_x      =  0.0;
logo_y      = 50.0;
logo_margin =  3.0;       // solid border kept clear of venting

// ---- Optional speaker: Pimoroni COM1602, 41x71x23mm -------
spk_enable   = false;
spk_len      = 71.0;   // long axis, runs across the tray (x)
spk_wid      = 41.0;   // short axis, runs along the tray (y)
spk_hole_x   = 63.5;   // centres along the long axis
spk_hole_y   = 33.5;   // centres along the short axis
spk_y0       = 101.0;  // rear edge of the speaker frame
spk_screw_d  =  3.20;  // front pair: M3 clearance, countersunk underneath
spk_cs_d     =  6.20;
spk_cs_depth =  1.60;
spk_peg_d    =  2.85;  // rear pair: locating pegs
spk_peg_h    =  4.00;

// ---- Derived ----------------------------------------------
rail_x  = bay_w/2 - rail_t/2;
pcb_hx  = pcb_hole_dx/2;
pcb_hy  = [pcb_hole_rear + pcb_y_offset,
           pcb_hole_rear + pcb_hole_pitch + pcb_y_offset];
fix_d   = use_inserts ? insert_d      : boss_pilot;
fix_dep = use_inserts ? insert_depth  : boss_depth;

spk_hx      = spk_hole_x/2;
spk_y_rear  = spk_y0 + (spk_wid - spk_hole_y)/2;
spk_y_front = spk_y_rear + spk_hole_y;

// ============================================================
//  Helpers
// ============================================================

module rrect(w, h, t, r = 3) {
    hull() for (dx = [-1, 1], dy = [-1, 1])
        translate([dx*(w/2 - r), dy*(h/2 - r), 0])
            cylinder(r = r, h = t);
}

module tslot(y) {
    hull() for (x = [-vent_x, vent_x])
        translate([x, y, -0.5]) cylinder(d = vent_w, h = base_t + 1);
}

module lslot(x, y0, y1) {
    hull() for (y = [y0, y1])
        translate([x, y, -0.5]) cylinder(d = vent_w, h = base_t + 1);
}

// ============================================================
//  Solids
// ============================================================

module base_plate() {
    translate([-bay_w/2, 0, 0]) cube([bay_w, bay_l, base_t]);
}

module rails() {
    for (s = [-1, 1])
        translate([s*rail_x - rail_t/2, 0, 0]) cube([rail_t, bay_l, rail_h]);
}

module front_wall() {
    translate([-bay_w/2, bay_l - front_t, 0]) cube([bay_w, front_t, rail_h]);
}

module pcb_bosses() {
    for (x = [-pcb_hx, pcb_hx], y = pcb_hy)
        translate([x, y, 0]) cylinder(d = boss_d, h = base_t + boss_h);
}

module speaker_pegs() {
    if (spk_enable)
        for (x = [-spk_hx, spk_hx])
            translate([x, spk_y_rear, base_t])
                cylinder(d1 = spk_peg_d, d2 = spk_peg_d - 0.6, h = spk_peg_h);
}

// ============================================================
//  Cutting tools
// ============================================================

module bay_bottom_holes() {
    for (x = [-bot_span/2, bot_span/2], y = bot_y)
        translate([x, y, -0.1]) cylinder(d = bay_pilot, h = bay_depth + 0.1);
}

module bay_side_holes() {
    for (s = [-1, 1], y = side_y)
        translate([s*(bay_w/2 + 1), y, side_z])
            rotate([0, -s*90, 0]) cylinder(d = bay_pilot, h = rail_t + 2);
}

module pcb_fixings() {
    for (x = [-pcb_hx, pcb_hx], y = pcb_hy)
        translate([x, y, base_t + boss_h - fix_dep])
            cylinder(d = fix_d, h = fix_dep + 0.1);
}

module speaker_holes() {
    if (spk_enable)
        for (x = [-spk_hx, spk_hx]) {
            translate([x, spk_y_front, -0.1])
                cylinder(d = spk_screw_d, h = base_t + 0.2);
            translate([x, spk_y_front, -0.01])   // countersink on the underside
                cylinder(d1 = spk_cs_d, d2 = spk_screw_d, h = spk_cs_depth);
        }
}

// 2D logo artwork scaled to logo_w
module logo_2d() { scale(logo_w/100) hddsynth_logo(); }

module logo_cut() {
    do_bottom = (logo_face == "bottom" || logo_face == "both");
    do_top    = (logo_face == "top"    || logo_face == "both");

    if (logo_style == "engrave") {
        // Underside: mirrored in x so it reads the right way round
        // when you are looking up at the bottom of the drive.
        if (do_bottom)
            translate([logo_x, logo_y, -0.01])
                linear_extrude(logo_depth + 0.01) mirror([1, 0, 0]) logo_2d();
        if (do_top)
            translate([logo_x, logo_y, base_t - logo_depth])
                linear_extrude(logo_depth + 0.01) logo_2d();
    } else if (logo_style == "panel") {
        if (do_bottom)
            translate([logo_x, logo_y, -0.01])
                rrect(logo_w, logo_h, logo_depth + 0.01);
        if (do_top)
            translate([logo_x, logo_y, base_t - logo_depth])
                rrect(logo_w, logo_h, logo_depth + 0.01);
    }
}

// Areas the venting must not eat into
module vent_keepouts() {
    for (x = [-pcb_hx, pcb_hx], y = pcb_hy)
        translate([x, y, -1]) cylinder(d = boss_d + 4, h = base_t + 2);
    if (logo_style != "none")
        translate([logo_x, logo_y, -1])
            rrect(logo_w + 2*logo_margin, logo_h + 2*logo_margin, base_t + 2);
    if (spk_enable)
        for (x = [-spk_hx, spk_hx], y = [spk_y_rear, spk_y_front])
            translate([x, y, -1]) cylinder(d = 11, h = base_t + 2);
}

module vents() {
    difference() {
        union() {
            for (y = [vent_y0 : vent_pitch : vent_y1]) tslot(y);
            for (s = [-1, 1], seg = out_seg) lslot(s*out_x, seg[0], seg[1]);
        }
        vent_keepouts();
    }
}

// ============================================================
//  Assembly
// ============================================================

module tray() {
    difference() {
        union() {
            base_plate();
            rails();
            front_wall();
            pcb_bosses();
            speaker_pegs();
        }
        bay_bottom_holes();
        bay_side_holes();
        pcb_fixings();
        vents();
        logo_cut();
        speaker_holes();
    }
}

module ghost_pcb() {
    %translate([-pcb_w/2, pcb_y_offset, base_t + boss_h])
        cube([pcb_w, pcb_l, pcb_t]);
}

module ghost_speaker() {
    if (spk_enable)
        %translate([-spk_len/2, spk_y0, base_t]) cube([spk_len, spk_wid, 23]);
}

tray();
if (show_pcb) { ghost_pcb(); ghost_speaker(); }
