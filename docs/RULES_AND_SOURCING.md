# Rules and sourcing in Tashkent

## 1. The rules come first

This is a summary of what public sources said in November 2026. It is not legal advice,
and the rules have been changing, so check them again before spending money.

**What the sources say**

- Uzbekistan prohibits the import, sale, purchase, storage and use of unmanned aerial
  vehicles **and their components and spare parts** without a permit
  (Cabinet of Ministers Resolution No. 658, 15 November 2022). Permits are for organisations.
- The Civil Aviation Agency's own page says these requirements **do not apply to aircraft
  models and toy aircraft models**. Toy models may fly below 50 m, in sight, at a safe distance
  from people and at least 150 m from airfield approach paths. Model aircraft flown for
  educational, sports, cultural or technical-creativity events may fly **only in designated zones**.
- Since March 2024 a first offence is an administrative offence with a fine; a repeat offence
  is criminal (Criminal Code, Article 244-4).
- A liberalisation announced in February 2026 concerns legal entities, not private individuals.

**What is not clear from those sources**

- The exact legal definition of an "aircraft model", and whether an 800 g radio-controlled
  plane built by a private person counts as one.
- Whether a brushless motor, ESC or RC transmitter ordered by post is treated by customs as a UAV component.

**What to do about it**

1. Run this as a **school or club technical-creativity project**, with a teacher or club leader
   responsible. That is the situation the model-aircraft exemption describes.
2. **Before buying any motor, ESC, radio or battery**, ask the Civil Aviation Agency
   (contacts on the page linked below) or an aeromodelling club how model aircraft are
   handled and where the designated flying zones are. The "Vatanparvar" organisation runs
   aeromodelling sport in Uzbekistan and is a good first call.
3. **Never fit a camera, FPV gear, GPS or an autopilot.** Those are what make an aircraft a drone.
   The optional Arduino flight logger in the brief records data on an SD card only: no camera, no radio link.
4. Fly only where model flying is allowed, far from airports, borders, military and government sites.
5. Until all of that is settled, build the **half-scale test glider** and the airframe.
   Foam, glue and printed parts are not restricted.

Sources:
[Civil Aviation Agency: Drones – UAV](https://gov.uz/en/uzcaa/pages/dronlar-uua) ·
[Kun.uz, penalties softened, March 2024](https://kun.uz/en/news/2024/03/16/uzbekistan-softens-responsibility-for-using-drones) ·
[Kun.uz, criminal liability, 2019](https://m.kun.uz/en/news/2019/02/28/criminal-liability-to-be-introduced-for-illegal-use-of-drones) ·
[Kun.uz, liberalisation for legal entities, February 2026](https://kun.uz/en/news/2026/02/18/uzbekistan-to-lift-ban-on-drone-imports-and-production-for-legal-entities) ·
[Tashkent khokimiyat warning, 2019](https://kun.uz/en/news/2019/11/01/tashkent-city-khokimiyat-warns-about-responsibility-for-using-drones) ·
[Resolution No. 658 on lex.uz](https://lex.uz/docs/6284992)

## 2. Airframe materials

Stock and prices were not checked shop by shop. The Russian names are what to ask for.

| Item | Qty | What to ask for | Notes |
|---|---|---|---|
| 5 mm paper-faced foam board | 3 sheets 500 x 700 mm, or 2 x A1 | пенокартон 5 мм | Sign-making, print and art-supply shops. The fuselage shell is 758 mm long: buy at least one A1 or 700 x 1000 mm sheet, or splice two pieces with a 60 mm foam doubler inside. |
| Spar | 1 m of 6 mm | круглая деревянная рейка / нагель 6 мм, or a 6 x 4 mm carbon tube | Cut into two 495 mm pieces. A straight bamboo garden cane also works. |
| Hot glue gun and sticks | 1 + 10 sticks | термоклеевой пистолет | Low-temperature glue is kinder to foam. |
| Clear packing tape | 1 roll | скотч упаковочный | Hinge reinforcement, leading edges, wing centre joint. |
| Bamboo skewers | 1 pack | шпажки бамбуковые | Wing band dowels (use two or three glued together for 6 mm), tail skid. |
| Rubber bands | 6–8 strong ones | резинки канцелярские | Hold the wing on. |
| Pushrod wire | 2 x 600 mm of 1.2–1.5 mm steel | сталистая проволока 1,2 мм | Bicycle spokes also work for short runs. |
| Landing gear wire | 300 mm of 3 mm steel | проволока стальная 3 мм | Optional: set `LANDING_GEAR = False` to hand-launch. |
| M3 hardware | 4 x M3x25, 4 x M3x20, 4 x M3x8, 8 nuts, 8 washers | винты М3 | Motor mount, gear block, motor. |
| Velcro strip | 200 mm | липучка | Battery and receiver. |
| PLA filament | about 100 g | | All printed parts together. |

**If you cannot get paper-faced foam board:** 5 mm XPS laminate underlay (подложка под ламинат)
or EPS ceiling tiles (потолочная плитка) are lighter but have no paper skin. Cover both faces
with packing tape before cutting, use tape for hinges instead of the paper, and add a second
spar strip. Weigh a sheet and set `FOAM_AREAL_DENSITY` in `params.py`, because the balance changes.

**Weigh your foam board first.** Mass in grams divided by area in m². The default is
500 g/m². Put your number in `params.py` and run `python build.py`: the nose length is
recalculated so the plane still balances.

## 3. Electronics (after section 1 is settled)

| Item | Spec | Why |
|---|---|---|
| Motor | 2212 outrunner, about 1000 KV | 144 W on 3S with a 9x4.7 prop: 184 W/kg |
| Propeller | 9x4.7 slow-fly, plus 3 spares | Pitch speed 2.1 x stall speed |
| ESC | 30 A with 5 V BEC | Motor draws about 13 A: plenty of margin |
| Battery | 3S (11.1 V) LiPo, 1500 mAh | About 11 minutes; 135 g sets the nose length |
| Charger | Balance charger + LiPo-safe bag | Never charge unattended |
| Servos | 4 x 9 g micro servos | 2 ailerons, elevator, rudder |
| Radio | 4+ channel 2.4 GHz transmitter and receiver | A buddy-box (trainer) port helps a lot |
| Extension leads | 2 x 300 mm servo extensions, 1 Y-lead | Aileron servos to the receiver |

If your motor's data sheet gives different thrust or current, put the numbers in
`params.py` (`MOTOR_STATIC_THRUST_G`, `MOTOR_MAX_CURRENT_A`) and rebuild.
