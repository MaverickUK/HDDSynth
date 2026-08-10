// ============================================================
//  HDD Synth MKV  ->  2.5" side-mount base plate
//  Bolts under the board and presents the SFF-8201 side
//  mounting holes, so the assembly mounts like a 2.5" drive.
//
//  Orientation: y=0 REAR (USB-C / connector datum),
//               z=0 is the bottom datum plane.
//  Print flat, no supports.
//
//  NOTE ON HEIGHT: SFF-8201 puts the side holes 3.00mm above
//  the bottom datum, at y = 14.00 / 90.60 - the *same* long-
//  itudinal positions as the board's own mounting holes. The
//  rail is therefore 10mm tall so the M3 pilot coming down
//  from the top stops ~1mm clear of the side hole below it.
//  Dropping rail_h below ~9 will make the two holes break
//  into each other. If you need a lower profile, set
//  modern_side_holes = false and use the legacy positions
//  only - those don't coincide with the board holes.
// ============================================================

$fn = 48;

show_pcb = false;

// ---- 2.5" form factor, SFF-8201 ---------------------------
ff_w   = 69.85;    // A4  width
ff_l   = 100.33;   // matches the HDD Synth outline (A6 max 100.45)
side_z =  3.00;    // A23 side hole height above the bottom datum

modern_side_holes = true;   // A52/A53: 14.00 / 90.60
legacy_side_holes = true;   // A30/A31: 34.93 / 73.03 (obsolete, still common)
side_y_modern = [14.00, 90.60];
side_y_legacy = [34.93, 73.03];

side_pilot = 2.80;   // M3 self-tap, no drilling
side_depth = 4.50;   // A38 requires >= 3.00mm penetration

// ---- HDD Synth MKV board ----------------------------------
pcb_w          = 69.85;
pcb_l          = 100.33;
pcb_t          =  1.60;
pcb_hole_dx    = 61.72;
pcb_hole_rear  = 13.97;
pcb_hole_pitch = 76.60;

// ---- Plate construction -----------------------------------
floor_t = 3.0;
rail_t  = 5.0;
rail_h  = 10.0;     // see note above
boss_d  = 8.0;

boss_pilot   = 2.80;
boss_depth   = 4.60;
use_inserts  = false;
insert_d     = 4.00;
insert_depth = 4.60;

// ---- Venting ----------------------------------------------
vent_w     =  9.0;
vent_x     = 20.0;
vent_pitch = 11.5;
vent_y0    =  9.0;
vent_y1    = 92.0;

// ---- Derived ----------------------------------------------
rail_x  = ff_w/2 - rail_t/2;
pcb_hx  = pcb_hole_dx/2;
pcb_hy  = [pcb_hole_rear, pcb_hole_rear + pcb_hole_pitch];
fix_d   = use_inserts ? insert_d     : boss_pilot;
fix_dep = use_inserts ? insert_depth : boss_depth;

side_y  = concat(modern_side_holes ? side_y_modern : [],
                 legacy_side_holes ? side_y_legacy : []);

// ============================================================

module tslot(y) {
    hull() for (x = [-vent_x, vent_x])
        translate([x, y, -0.5]) cylinder(d = vent_w, h = floor_t + 1);
}

module floor_plate() {
    translate([-ff_w/2, 0, 0]) cube([ff_w, ff_l, floor_t]);
}

module rails() {
    for (s = [-1, 1])
        translate([s*rail_x - rail_t/2, 0, 0]) cube([rail_t, ff_l, rail_h]);
}

module fix_bosses() {
    for (x = [-pcb_hx, pcb_hx], y = pcb_hy)
        translate([x, y, 0]) cylinder(d = boss_d, h = rail_h);
}

module side_holes() {
    for (s = [-1, 1], y = side_y)
        translate([s*(ff_w/2 + 0.1), y, side_z])
            rotate([0, -s*90, 0]) cylinder(d = side_pilot, h = side_depth);
}

module pcb_fixings() {
    for (x = [-pcb_hx, pcb_hx], y = pcb_hy)
        translate([x, y, rail_h - fix_dep]) cylinder(d = fix_d, h = fix_dep + 0.1);
}

module vent_keepouts() {
    for (x = [-pcb_hx, pcb_hx], y = pcb_hy)
        translate([x, y, -1]) cylinder(d = boss_d + 4, h = floor_t + 2);
}

module vents() {
    difference() {
        union() { for (y = [vent_y0 : vent_pitch : vent_y1]) tslot(y); }
        vent_keepouts();
    }
}

module plate() {
    difference() {
        union() { floor_plate(); rails(); fix_bosses(); }
        side_holes();
        pcb_fixings();
        vents();
    }
}

plate();
if (show_pcb)
    %translate([-pcb_w/2, 0, rail_h]) cube([pcb_w, pcb_l, pcb_t]);
