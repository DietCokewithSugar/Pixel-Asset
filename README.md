# 肉鸽动物八方向精灵

九种进化角色的可爱像素精灵，按 [pixel-asset-master](skills/pixel-asset-master/SKILL.md) 的规格生成。每只动物都有八个朝向，以及原地静息、移动、快速移动、攻击、受伤。

打开预览（可切换角色、朝向、动作，并下载图集）：

```bash
python3 -m http.server 8765
```

浏览器访问 [http://127.0.0.1:8765/](http://127.0.0.1:8765/) 。

游戏图集在 `projects/rogue_animals_64x64_20261021/sheets/game/`。每张图 64×64，一行一个朝向（下、右下、右、右上、上、左上、左、左下），一列一帧。全部打包文件是 `projects/rogue_animals_64x64_20261021/exports/rogue_animals_sprites.zip`。
