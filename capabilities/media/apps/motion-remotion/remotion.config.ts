import {Config} from '@remotion/cli/config';

Config.setCodec('h264');
Config.setCrf(18);
Config.setPixelFormat('yuv420p');
Config.setColorSpace('bt709');
Config.setMuted(true);
Config.setOverwriteOutput(true);
Config.setLogLevel('warn');
