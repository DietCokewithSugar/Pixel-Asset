# Execution Lock

## canvas
- base_size: 64x64
- tile_size: 64x64
- format: RGBA PNG

## palette
- name: Cute Rogue 32
- colors:
  - #1A1C2C
  - #333C57
  - #566C86
  - #94B0C2
  - #F4F4F4
  - #FFD6E0
  - #FFF3C4
  - #FFCD75
  - #EF7D57
  - #C45C26
  - #B13E53
  - #7A2438
  - #E8D0FF
  - #C4A1E8
  - #7A5AAA
  - #73EFF7
  - #41A6F6
  - #3B5DC9
  - #29366F
  - #1A2744
  - #F6E7C1
  - #D7C4A3
  - #A7F070
  - #38B764
  - #1E6B3A
  - #D4F5A0
  - #8FD96A
  - #2F6B32
  - #0E4A28
  - #146B3A
  - #3FA868
  - #5D275D

## style
- sub_style: outlined
- outline_color: #1A1C2C
- shading: 3-tone
- dithering: none
- light_direction: top-left
- mood: cute chibi, simplified animal features, not realistic

## per_sprite_budget
- max_colors: 16

## facing
- mode: 8-dir
- order: down, downright, right, upright, up, upleft, left, downleft
- composition: upright character, head toward top of frame, feet toward bottom

## animation
- idle: frames 4, fps 6, loop true
- walk: frames 6, fps 8, loop true
- run: frames 6, fps 12, loop true
- attack: frames 4, fps 10, loop false
- hurt: frames 2, fps 8, loop false

## assets
- characters:
  - name: mini_scorpion
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: venom_scorpion
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: whip_spider
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: egg_raptor
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: feather_raptor
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: cassowary
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: little_cat
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: false_cat
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
  - name: lion_boss
    size: 64x64
    colors: all
    animations: idle,walk,run,attack,hurt
- tiles: []
- items: []
- ui: []
- effects: []
- backgrounds: []

## forbidden
- Anti-aliasing
- Gradient fills
- Partial opacity (1-254 alpha)
- Colors outside declared palette
- Sub-pixel rendering
