# Streetlight Night Environment

Main file: `blend_files/streetlight_night_environment_final.blend`

The scene keeps the original streetlight geometry and adds:

- procedural PBR asphalt, concrete, curb, sidewalk, markings, dirt, patches, and subtle cracks;
- warm streetlight illumination with soft shadows, a true volumetric beam, haze, and lamp glow;
- lightweight animated instanced dust and insect rigs;
- an Eevee cinematic camera and real-time-friendly render settings.

Folders:

- `blend_files/` — original, textured, and final scene files;
- `blend_files/archive/` — intermediate/library and Blender backup files;
- `renders/` — inspection, material, and final night renders;
- `scripts/` — reproducible Blender build, texturing, inspection, and preview scripts.

The final scene's render output is configured for `../renders/` relative to the final `.blend`.
