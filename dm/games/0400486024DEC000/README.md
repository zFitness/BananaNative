# The Legend of Zelda: Ocarina of Time (`0400486024DEC000`)

A Switch 2 game: the base game v65536 over an update v131072 (2.0.0), SDK 22.2.8 built for the Switch 2 (`sdk` names its spec `Ounce`), NVN2. Nintendo EPD's engine (sead / agl / gsys, Phive, Havok, CRIWARE), modules `main` + `subsdk0` (NintendoSDK_movie) + `sdk`. **In bring-up on Android** (Lenovo TB322FC, Adreno 830): the code is rewritten and the shaders are translated, the game boots, takes its heap and reaches its graphics module's init, where it stops on a NULL read because the dump it is given is missing files ([The dump is missing files](#the-dump-is-missing-files)); nothing past that is tested yet.

## What it needs

| Setting | Where | Why |
|---|---|---|
| `modules main subsdk0 sdk` | [`game.tsv`](game.tsv) | the survey's guess, checked against the modules' imports: `main` takes nothing from the `subsdk0` (the movie player), and the host replaces `rtld` |
| `romfs_marker System/RegionLangMask.txt` | `game.tsv` | a file every version has |
| `romfs_check System/RegionLangMask.txt 4 main` | `game.tsv` | the file's fourth line is the build ID of the `main` its RomFS was made for (`e0f3ccfaf50065ae4ea01eb5aeb13b1a` for update v131072), so a folder with the base game's data is told from one with the update's |
| `mem_reserve 0x240000000`, `mem_alias 0x118000000`, `mem_stack 0x10000000`, `app_pool 0x180000000` | `game.tsv` | a 0x240000000 (8.8 GiB) block with a 0x118000000 (4.4 GiB) alias region, 256 MiB of stacks and a 0x180000000 (6 GiB) application pool: the game asks for its heap in `nninitStartup` (`main+0x260bb10`), reading `nn::os::QueryMemoryInfo` for it, so the block has to hold the heap (3.20 GiB, out of a 4.12 GiB heap region) and the address-region memory the game maps in the alias region (the log: `alias region mapped up to +1.50 GB (alias region 4.38 GB)`, `alias region mapped 0.50 GB (application pool 6.00 GB)`). The survey's 5 GB guess had no room for the heap |
| `sys_resource 0x3000000` | `game.tsv` | the NPDM declares 48 MB of system resource: virtual address memory on |

## Files

- Built from a dump in one `.nup` file (the [NUP](../../../android/NUP.md) container: `base` v65536 and `update` v131072, no add-ons), 25.6 GB. The package's files are stored raw (codec 0): the game's own compression is one zstd frame per file (`.zs`), which the game reads itself, so the host serves the bytes as they are.
- The update's RomFS: 186,583 files and 26.24 GB, of which 102,185 are zstd frames (16.5 GB), 26,378 Wwise banks (`.bwav`, 2.0 GB) and 46,324 extension modules (`.extm`).
- The shaders are the engine's: BNSH in `Shader/*.bfsha.zs` (Model, Foliage, SceneMaterial, TerrainGround) and the `Shader/ApplicationPackage.Nin_Ounce_NVN2.release.sarc.zs` archive, with the effects in `Effect/` and the layouts in `UI/` — the same layout as the other Switch 2 games'.
- The code modules are ZBIC-compressed (system 22.0.0+, Nintendo's zstd variant): `dm/tools/nso.py` reads them with the `zbic` package, which the phone's packer does not have ([Boot (Android)](#boot-android).
- The dump is short of the product: [The dump is missing files](#the-dump-is-missing-files).

## The dump is missing files

The game stops in its graphics module's init with a NULL read, and the log before it says which files it could not open:

```
fs open not found: content:/Pack/GeneralFormat/Global.Product.gfpack.byml.zs
fs open not found: content:/Tex/Fire_Thick_Burst_00_Dst.bntx.zs
fs open not found: content:/Tex/Fire_Thick_Burst_00_Fia.bntx.zs
CRASH sig=11 addr=0 pc=main+0x31bd480
```

Those files are not in the dump, and the game's own data says they should be. The check is on the container itself, not on the host: the `.nup`'s table of contents was pulled out (36.8 MB) and both packages' trees rebuilt from it (the name pool holds base names, the directories are separate records).

- **The container holds exactly what its table of contents lists.** All 372,587 file records (both packages, every one stored raw) point into the container's blob region; merging their extents covers 25,584,358,434 of its 25,585,449,364 bytes, so 1.09 MB (0.004 %) is unreferenced padding. Nothing is in the container that the table does not name, and nothing the table names is missing from the blob.
- **The files the game asked for are in neither package.** Rebuilt paths, case-insensitively: `Pack/GeneralFormat/` 0, `*.gfpack*` 0, `Fire_Thick*` 0, `ModuleInitializeParam*` 0, `Noise_Perlin_Distrotion_03*` 0. The `Noise_Perlin_Distrotion` family has only `_01_Dst` and `_02_Dst`, and `Pack/` has twelve loose files and one directory (`Pack/Actor/`, 8,373 files) but no `GeneralFormat`.
- **The game ships its own list of the product's files:** `System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs` (`RESTBL`, version 1) holds 219,968 entries and names ten of them. The dump holds 186,583 files in the update, 185,994 in the base, 186,808 in the two together (225 base-only, 814 update-only). Three of the ten named paths are in neither package, and their base names are nowhere in the dump: `Actor/Land_ShadowTemple_DoorJointParts_B_01.engine__actor__ActorParam.bgyml`, `Life/DamageParameters/BombFlower_Fruit.game__life__DamageParameters.bgyml` and `Phive/ShapeParam/Obj_TimeTemple_WarpPoint_A_01__StairStep.phive__ShapeParam.bgyml`. (Its size column sums to 60.13 GB; what the numbers are exactly is not known — a sample of 80 textures' decompressed sizes are mostly not among them.)

The dump is therefore short of the product, by about 33,000 files if the table's entries are one per file. The crash is the game's own code using a material table it never filled, and the game's code says why:

- The general-format data is a loose file, not a member of a pack: every pack in the dump (the twelve under `Pack/`, and the 8,373 under `Pack/Actor/`) was opened and its members listed, and none of them holds a `GeneralFormat` or `gfpack` member. The game asks for the file by path (`content:/Pack/GeneralFormat/Global.Product.gfpack.byml`), so on a console it is a file of the product's RomFS.
- The graphics module's init (`main+0x31bca20`) reads the material list out of that data and then writes into its first entry without asking whether the list has one: the list's count is at `[this+0x1d0]` and its data pointer at `[this+0x1d8]` (`str w22, [x20, #0x1d0]` / `str x0, [x20, #0x1d8]` at `main+0x31bd280`); with the data missing the list stays empty (count 0, data NULL), the loop still takes element 0 (`csel w8, w26, wzr, lo` at `main+0x31bd3c4`, `smaddl x24, w8, x10, x9` at `+0x31bd3c8`) and the first write into it, `ldrb w8, [x24]` at `main+0x31bd480`, faults at address 0.

So the fault is the missing general-format data, not a host bug, and the host cannot fix it: the files have to come from a complete dump ([A dump that is missing files crashes the game](../../../docs/reference/packing.md#a-dump-that-is-missing-files-crashes-the-game)).

One host gap turned up on the way, not the cause of this crash: the pack mounts the update package alone (`pack.tsv`'s `…nup:update/131072/romfs`), and `nup_image.h` opens one package, so the 225 base-only files (the `Product.100` versions the update replaced) are not served at all. For this game that is harmless — the update carries the `Product.111` versions of all of them — but it is a gap in the layered view a console has.


## Shaders

42,321 shaders (22,356 pixel, 15,852 vertex, 4,101 compute, 9 mesh, 3 task), split from the update's RomFS and the `main` module: 22,403 in the effect group, 14,204 in the shader group, 5,714 elsewhere. The nine mesh and three task programs are Switch 2's geometry shaders; one mesh program (`2582bd7ea6490d33`) the split could not map: its output map holds outputs besides the position and the generic vectors, whose planes are not known, so it is left out. On the Vulkan replay 42,228 of the 42,321 translate (19 fail to translate, 74 fail the SPIR-V validator), among them 10 of the 12 mesh and task programs.

The Vulkan library is built by `dm/gfx/tools/vk_android_build.py` (chain `v-31b81e5c07ac`), the same chain the other Switch 2 games use. The phone's own split of the dump finds one shader more than the profile's map holds (42,322 against 42,321), so the library is one shader short of what the dump holds; which shader it is, is not known yet (the split's map is on the phone).

## Boot (Android)

The game's files stay on the phone: the pack holds the rewritten code and the shader library, and the RomFS is the `.nup` itself (`DM_ROMFS` takes it in place, [NUP](../../../android/NUP.md)).

The code is rewritten on the Mac (the rewriter needs the `zbic` package for the ZBIC modules) and the shader library is built there too; the phone's own packer cannot rewrite ZBIC modules, and the shader build on the phone is about five times slower than on the Mac.

On the phone (Lenovo TB322FC, Android 16, Adreno 830; the driver's Turnip, `Turnip_Gen8_V38`, through `DM_VK_DRIVER`; the launcher's readiness check PASSes with 14.8 GiB of RAM):

1. The heap was the first wall: with the survey's 5 GB block the game asked for its heap and the host had no room for it. With the profile's 0x240000000 block it asks for 3.20 GiB and gets it (`heap 3.20 GB (heap region 4.12 GB)`), maps 0.50 GB of the application pool and 1.50 GB of the alias region, and reaches its graphics module's init.
2. With the system's driver the launcher's readiness check failed (no placed maps), so nothing was drawn; with Turnip it passes, the placed maps work and the game runs to its crash.
3. The crash: [The dump is missing files](#the-dump-is-missing-files).

## Open

- The dump is short of the product by about 33,000 files, so the game cannot get past its graphics module's init; a complete dump is needed before anything else is tested ([The dump is missing files](#the-dump-is-missing-files)).
- The game is not tested past that point: no scene, no sound, no input.
- The `sdk` build's two function-matched patches do not apply (they match no function in SDK 22.2.8): the address arbiter's node area and `AllocateAddressRegion`'s alignment. Whether the game needs them (Tears of the Kingdom does, for its alias region) is open.
- The game's texture formats are not known yet (the crash comes before its first texture upload), so what the phone's GPU has to support for them (BC7, ASTC) is open.
- The phone's Turnip has no `VK_EXT_mesh_shader`, so the draws of the 9 mesh programs are skipped; what the scene loses in them is not measured.

## Found on this game

- The split's mesh-program check rejects a mesh program whose output map has more than the position and the generic vectors (`2582bd7ea6490d33`): the planes of the other outputs are not known.
- [A dump that is missing files crashes the game](../../../docs/reference/packing.md#a-dump-that-is-missing-files-crashes-the-game): the game's own size table (`ResourceSizeTable.Product.111`) against the dump's file list.
