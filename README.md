# AviSynth-Plugins-AUR

Linux packaging for AviSynth/VapourSynth plugins via GitHub Actions.

1. Publishes Linux builds in Releases for Arch and Ubuntu 22.04.
2. Publishes in AUR, self-compile and -bin variant for large packages.
3. Tracks new releases to update builds.

## Packages

**avisynth-plugin-rife-asdg / -bin**: [Asd-g RIFE](https://github.com/Asd-g/AviSynthPlus-RIFE). Models not included — unpack [the pack](https://github.com/Asd-g/AviSynthPlus-RIFE/releases/tag/models) into `/usr/lib/avisynth/models/` or pass `model_path`.  
**avisynth-plugin-mvtools2-pinterf / -bin** [pinterf](https://github.com/pinterf/mvtools)  
**avisynth-plugin-xclean**: [xClean](https://github.com/mysteryx93/xClean) AVSI. VapourSynth is already `vapoursynth-plugin-xclean-git`.

## Add a plugin

If you want to add a plugin to the build pipeline, open an Issue with the repo URL. For either AviSynth or VapourSynth. New builds can be added to the pipeline quite easily, and it will update itself.

## License

MIT packaging. Each plugin keeps its upstream license.