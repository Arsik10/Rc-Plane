"""
params.py - every INPUT of the design lives here.

Change a value, run `python build.py`, and the sizing report, the 1:1 foam
templates, the STL files and the drawings are all regenerated to match.

Units: millimetres, grams, degrees unless the name says otherwise.
"""

# --------------------------------------------------------------------------
# 1. Targets (the calculator warns when the design falls outside these)
# --------------------------------------------------------------------------
AUW_TARGET_MIN_G = 700          # all-up weight target window
AUW_TARGET_MAX_G = 900
WING_LOADING_MIN = 30.0         # g/dm^2
WING_LOADING_MAX = 45.0
STALL_SPEED_MAX = 9.0           # m/s
THRUST_TO_WEIGHT_MIN = 0.8
POWER_LOADING_MIN = 150.0       # W/kg, trainer guideline
POWER_LOADING_MAX = 200.0
STATIC_MARGIN_MIN = 0.10        # fraction of chord
STATIC_MARGIN_MAX = 0.15

# --------------------------------------------------------------------------
# 2. Flying site (air density changes the stall speed)
# --------------------------------------------------------------------------
FIELD_ELEVATION_M = 450         # Tashkent is roughly 450 m above sea level
AIR_TEMP_C = 25                 # a warm, calm morning

# --------------------------------------------------------------------------
# 3. Wing
# --------------------------------------------------------------------------
WINGSPAN = 1000.0
CHORD = 200.0                   # constant chord
CL_MAX = 1.1                    # Clark Y at model-size Reynolds numbers
DIHEDRAL_DEG = 4.0              # each wing half is raised by this angle
AILERON_CHORD_FRAC = 0.25       # of wing chord
AILERON_SPAN_FRAC = 0.45        # of each half-span, at the outer end
AILERON_TIP_MARGIN = 10.0       # fixed strip left at the tip
SPAR_CHORD_FRAC = 0.28          # spar position from the leading edge
SPAR_DIAMETER = 6.0             # carbon tube or wooden dowel
SPAR_MASS_G_PER_M = 20.0        # 6 mm dowel ~16 g/m, 6x4 carbon tube ~24 g/m
RIBS_PER_HALF = 5
TOP_SKIN_FLAT_FROM = 0.45       # top skin follows Clark Y up to here, then
                                # runs straight down to the hinge line

# --------------------------------------------------------------------------
# 4. Tail (sized from tail-volume coefficients)
# --------------------------------------------------------------------------
TAIL_ARM_CHORDS = 2.5           # wing 1/4-chord to tail 1/4-chord, in chords
VH = 0.50                       # horizontal tail volume coefficient
VV = 0.040                      # vertical tail volume coefficient
HTAIL_ASPECT_RATIO = 3.5
VTAIL_ASPECT_RATIO = 1.4        # height^2 / area
VTAIL_TAPER = 0.6               # tip chord / root chord
ELEVATOR_CHORD_FRAC = 0.35
RUDDER_CHORD_FRAC = 0.35

# --------------------------------------------------------------------------
# 5. Balance
# --------------------------------------------------------------------------
CG_FRAC = 0.27                  # design CG, fraction of chord from the LE
CG_FIRST_FLIGHT_FRAC = 0.25     # slide the battery forward for flight no. 1

# --------------------------------------------------------------------------
# 6. Fuselage (foam-board box)
# --------------------------------------------------------------------------
FUSE_WIDTH = 64.0               # outside
FUSE_HEIGHT = 75.0              # outside, nose to wing trailing edge
FUSE_TAIL_HEIGHT = 35.0         # outside, at the tail end
BAND_DOWEL_DIAMETER = 6.0       # skewers / dowels that hold the wing bands

# --------------------------------------------------------------------------
# 7. Sheet material
# --------------------------------------------------------------------------
FOAM_THICKNESS = 5.0
# WEIGH YOUR OWN SHEET: mass in grams / (length_m * width_m).
# Light hobby board is ~300, heavy display board 500-650.
FOAM_AREAL_DENSITY = 500.0      # g/m^2

# --------------------------------------------------------------------------
# 8. Power system (replace the bench numbers with your motor's data sheet)
# --------------------------------------------------------------------------
MOTOR_KV = 1000                 # rpm per volt, 2212-size outrunner
MOTOR_MASS_G = 58
MOTOR_DIAMETER = 28.0
MOTOR_LENGTH = 30.0
MOTOR_HOLE_SPACING = (16.0, 19.0)   # M3 back-mount pattern of 22xx motors
PROP_DIAMETER_IN = 9.0
PROP_PITCH_IN = 4.7
PROP_MASS_G = 9
MOTOR_STATIC_THRUST_G = 680     # with the prop above on 3S (bench figure)
MOTOR_MAX_CURRENT_A = 13.0      # at full throttle with that prop
ESC_RATING_A = 30
ESC_MASS_G = 28
BATTERY_CELLS = 3
BATTERY_MAH = 1500
BATTERY_MASS_G = 135
BATTERY_LENGTH = 75.0
CRUISE_CURRENT_A = 6.5          # average over a relaxed flight
RIGHT_THRUST_DEG = 2.5
DOWN_THRUST_DEG = 1.5

# --------------------------------------------------------------------------
# 9. Radio gear
# --------------------------------------------------------------------------
SERVO_MASS_G = 11               # 9 g servo + lead, horn and screws
RECEIVER_MASS_G = 10
# 9 g micro servo body (SG90 style)
SERVO_BODY = (22.8, 12.2, 22.7)     # length, width, height below the top
SERVO_TAB_SPAN = 32.5
SERVO_HOLE_SPACING = 27.6
SERVO_TAB_HEIGHT = 15.9             # underside of tabs above servo bottom

# --------------------------------------------------------------------------
# 10. Landing gear (set to False to hand-launch and belly-land)
# --------------------------------------------------------------------------
LANDING_GEAR = True
GEAR_WIRE_DIAMETER = 3.0
GEAR_TRACK = 200.0
WHEEL_DIAMETER = 55.0
GEAR_MASS_G = 45                # wire + two wheels + block
PROP_GROUND_CLEARANCE = 20.0

# --------------------------------------------------------------------------
# 11. Other masses (g)
# --------------------------------------------------------------------------
PRINTED_NOSE_MASS_G = 30        # firewall + motor mount + screws
PRINTED_JOINER_MASS_G = 10
PRINTED_SMALL_PARTS_MASS_G = 16 # servo tray, cradles, horns, dowel plates
PUSHRODS_MASS_G = 15
GLUE_TAPE_MASS_G = 50           # hot glue, packing tape, velcro, bands

# --------------------------------------------------------------------------
# 12. 3D printer
# --------------------------------------------------------------------------
PRINTER_BED = (220.0, 220.0, 250.0)
NOZZLE = 0.4
MIN_WALL = 1.2
M3_CLEARANCE = 3.4
M3_HEAD_DIAMETER = 6.2
