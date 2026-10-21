# Rogue Animals - Design Spec

> Human-readable design narrative. Machine-readable contract: spec_lock.md.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | rogue_animals |
| **Canvas Size** | 64x64 |
| **Asset Count** | 9 characters, 1584 frames |
| **Art Style** | Cute chibi modern pixel, outlined, 3-tone cel |
| **Target Platform** | Web preview + engine-agnostic PNG (Unity / Godot) |
| **Color Palette** | Cute Rogue 32 |
| **Created Date** | 2026-10-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Base sprite size** | 64x64 |
| **Tile size** | 64x64 |
| **Background size** | n/a |
| **Transparency** | Alpha channel (RGBA), only 0 or 255 |

Upright eight-direction composition: head stays toward the top of the frame and feet toward the bottom. Facing is readable from the face, snout, claws, and limb direction.

---

## III. Color Palette

### Palette Name: Cute Rogue 32

Extended from the built-in Sweetie 16 cute/chibi palette so each animal can keep a distinct body color while sharing ink, eyes, and blush.

| Index | HEX | Role |
| ----- | --- | ---- |
| 0 | #1A1C2C | Ink outline, pupils |
| 1 | #333C57 | Ground shadow |
| 2 | #566C86 | Slate |
| 3 | #94B0C2 | Gray blue |
| 4 | #F4F4F4 | Eye white, hit flash |
| 5 | #FFD6E0 | Blush |
| 6 | #FFF3C4 | Cream |
| 7 | #FFCD75 | Gold / yellow mid |
| 8 | #EF7D57 | Orange |
| 9 | #C45C26 | Orange shadow |
| 10 | #B13E53 | Deep red light |
| 11 | #7A2438 | Deep red shadow |
| 12 | #E8D0FF | Lilac light |
| 13 | #C4A1E8 | Lilac |
| 14 | #7A5AAA | Lilac shadow |
| 15 | #73EFF7 | Cyan / casque light |
| 16 | #41A6F6 | Sky blue |
| 17 | #3B5DC9 | Blue shadow |
| 18 | #29366F | Navy |
| 19 | #1A2744 | Black blue |
| 20 | #F6E7C1 | Eggshell |
| 21 | #D7C4A3 | Eggshell shadow |
| 22 | #A7F070 | Lime |
| 23 | #38B764 | Green |
| 24 | #1E6B3A | Green shadow |
| 25 | #D4F5A0 | Pale green |
| 26 | #8FD96A | Leaf |
| 27 | #2F6B32 | Leaf shadow |
| 28 | #0E4A28 | Mane shadow |
| 29 | #146B3A | Mane |
| 30 | #3FA868 | Mane light |
| 31 | #5D275D | Plum |

### Palette Usage Rules

- All sprite pixels MUST use colors from this palette
- Per-sprite color budget: 16 colors (excl. transparency)
- Light source direction: top-left
- Shading is 3 flat bands. No dithering, no gradients

---

## IV. Art Style Definition

| Property | Value |
| -------- | ----- |
| **Sub-style** | Outlined + cel-shaded |
| **Outline color** | #1A1C2C |
| **Shading depth** | 3-tone |
| **Dithering** | None |
| **Light direction** | Top-left |
| **Mood** | Cute, round, simplified. Features come from the real animal but are not realistic |

Silhouette first: each animal keeps one or two exaggerated traits from the character sheet.

---

## V. Asset List

### Characters

| Asset | Size | Colors | Animation | Description | Priority |
| ----- | ---- | ------- | --------- | ----------- | -------- |
| mini_scorpion | 64x64 | palette | idle walk run attack hurt | 迷拟蝎。伪拟蝎。橙色，圆滚滚的腹部，短小钳子 | high |
| venom_scorpion | 64x64 | palette | idle walk run attack hurt | 注毒拟蝎。拟蝎。黄色，短但很粗的钳子 | high |
| whip_spider | 64x64 | palette | idle walk run attack hurt | 霸王鞭蛛。鞭蛛。深红色，又长又粗的钳子，第一对足是长鞭 | high |
| egg_raptor | 64x64 | palette | idle walk run attack hurt | 手盗龙宝宝。浅蓝色，四肢短小，头顶碎蛋壳 | high |
| feather_raptor | 64x64 | palette | idle walk run attack hurt | 阔羽盗龙。浅紫色，短头冠，前肢长羽毛 | high |
| cassowary | 64x64 | palette | idle walk run attack hurt | 暴走鹤鸵。浅蓝头冠，黑蓝身体，强壮大腿 | high |
| little_cat | 64x64 | palette | idle walk run attack hurt | 小古猫。细齿兽。绿色，细长优雅 | high |
| false_cat | 64x64 | palette | idle walk run attack hurt | 假虎猫。假猫属。浅绿色，身体粗壮 | high |
| lion_boss | 64x64 | palette | idle walk run attack hurt | 狮老大。深绿色鬃毛，橙色身体，头和鬃毛很大 | high |

### Tiles

No tile assets in this batch.

### Items

No item assets in this batch.

### UI

No UI chrome assets. Preview page is a separate HTML tool.

### Effects

No standalone effect assets. Hurt flash is drawn inside the character frames.

### Backgrounds

No background assets. Sprites are transparent.

---

## VI. Animation Specification

| Asset | Animation | Frames | FPS | Loop | Notes |
| ----- | --------- | ------ | --- | ---- | ----- |
| all characters | idle | 4 | 6 | yes | 原地静息，呼吸起伏，偶尔眨眼 |
| all characters | walk | 6 | 8 | yes | 移动，步伐循环 |
| all characters | run | 6 | 12 | yes | 快速移动，步幅更大并前倾 |
| all characters | attack | 4 | 10 | no | 蓄力、击出、保持、收回 |
| all characters | hurt | 2 | 8 | no | 第一帧闪白，身体后仰 |

Directions, one row each on the game sheet: down, downright, right, upright, up, upleft, left, downleft.

Attack emphasis:

| Character | Strike |
| --------- | ------ |
| mini_scorpion | short pincers snap |
| venom_scorpion | thick pincers snap |
| whip_spider | long pincers lunge, whips sweep |
| egg_raptor | headbutt, tiny limbs |
| feather_raptor | feathered forelimbs sweep |
| cassowary | strong-leg kick |
| little_cat | claw swipe |
| false_cat | heavy paw swipe |
| lion_boss | mane-forward paw swipe |

---

## VII. Technical Constraints

- No anti-aliasing
- No gradient fills
- No partial opacity (fully opaque or transparent only)
- All colors from declared palette
- Consistent top-left light
- Pixel-perfect at 64x64
- Hard ink outline on body parts
- Left and right facings are constructed, not copied with a flipped light

---

## VIII. Platform Export Notes

| Platform | Special Requirements |
| -------- | ------------------- |
| Web preview | `preview/index.html` plays rows by direction and can download sheets |
| Godot / Unity | Slice `sheets/game/<id>_<action>.png` as 64x64. Rows are directions. Columns are frames |
| Zip | `exports/rogue_animals_sprites.zip` and per-character zips |
