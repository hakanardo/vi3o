"""
The following is a modified (and modernized to deal with python3) version of ffprobe.py from https://pypi.org/project/ffprobe/.
Unfortunately that project has not been maintained since 2013. It was/is distributed under an MIT license.

The following code is based on release 0.5 / Oct 30, 2013
"""
import subprocess
import re
from vi3o.compat import pathlib
import os


class FFProbeException(Exception):
    pass


class FFProbe:
    """ffprobe reader for video files

    OBS! This class assumes that ffprobe binary is found in your path,
    be careful when using this class that it might not always be the
    case..
    """
    def __init__(self, video_file):
        video_file = pathlib.Path(video_file)
        self.verify_binary()

        if not video_file.exists():
            raise FileNotFoundError('No such media file %s' % str(video_file))

        self.format = None
        self.created = None
        self.duration = None
        self.start = None
        self.bitrate = None
        self.streams = []
        self.video = []
        self.audio = []
        datalines = []

        proc = subprocess.Popen(
                ["ffprobe -show_streams %s" % str(video_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
        )

        self._parse_output(proc)
        self._reference_streams()

        proc.stdout.close()
        proc.stderr.close()

    def _parse_output(self, proc):
        """Read all the output lines and store each stream meta data

        The output will print the info for all streams separated with the
        [STREAM] and [/STREAM] markers. Parse the lines in between them and
        store each as an FFStream object in the self.streams list.
        """
        for line in iter(proc.stdout.readline, b''):
            if re.match(b'\[STREAM\]', line):
                datalines=[]
            elif re.match(b'\[\/STREAM\]', line):
                self.streams.append(FFStream(datalines))
                datalines=[]
            else:
                datalines.append(line.decode("utf-8"))

    def _reference_streams(self):
        """Set the video and audio streams
        """
        for stream in self.streams:
            if stream.is_audio:
                self.audio.append(stream)
            if stream.is_video:
                self.video.append(stream)

    def verify_binary(self):
        try:
            with open(os.devnull, 'w') as tempf:
                subprocess.check_call(["ffprobe","-h"], stdout=tempf, stderr=tempf)
        except OSError:
            raise IOError('ffprobe command not found in PATH.')


class FFStream:
    """
    An object representation of an individual stream in a multimedia file.
    """
    def __init__(self, datalines):
        # Add each key value pair to the object dict so that they
        # are directly accessable without implementing getter functions.
        # This allows us to reflect all fields from ffprobe with no
        # knowledge of them, but on the other hand with no error checking
        # or format conversion. Thus we prefix with underscore.
        for line in datalines:
            (key, val) = line.strip().split('=')
            self.__dict__["_%s" % key] = val

        # Some fields that are strings can be marked as safe:
        safe = [
                "codec_name",
                "codec_long_name",
                "pix_fmt",
        ]
        for key in safe:
            self.__dict__[key] = self.__dict__.get("_%s" % key)

    @property
    def is_audio(self):
        """
        Is this stream labelled as an audio stream?
        """
        val=False
        if self.__dict__['_codec_type']:
            if str(self.__dict__['_codec_type']) == 'audio':
                val=True
        return val

    @property
    def is_video(self):
        """
        Is the stream labelled as a video stream.
        """
        val=False
        if self.__dict__['_codec_type']:
            if self._codec_type == 'video':
                val=True
        return val

    @property
    def is_subtitle(self):
        """
        Is the stream labelled as a subtitle stream.
        """
        val=False
        if self.__dict__['_codec_type']:
            if str(self._codec_type)=='subtitle':
                val=True
        return val

    @property
    def frame_size(self):
        """
        Returns the pixel frame size as an integer tuple (height, width) if the stream is a video stream.
        Returns None if it is not a video stream.
        """
        size=None
        if self.is_video:
            h = self.__dict__['_height']
            w = self.__dict__['_width']
            if h and w:
                try:
                    size=(int(h), int(w))
                except ValueError:
                    raise FFProbeException("None integer size %s:%s" %(str(h), str(w)))
        return size

    @property
    def pixel_format(self):
        """
        Returns a string representing the pixel format of the video stream. e.g. yuv420p.
        Returns none is it is not a video stream.
        """
        f=None
        if self.is_video:
            if self.__dict__['pix_fmt']:
                f=self.__dict__['pix_fmt']
        return f

    @property
    def frames(self):
        """
        Returns the length of a video stream in frames. Returns 0 if not a video stream.
        """
        f=None
        if self.is_video or self.is_audio:
            if self.__dict__['_nb_frames']:
                try:
                    f=int(self.__dict__['_nb_frames'])
                except ValueError:
                    raise FFProbeException("None integer frame count")
        return f

    @property
    def duration_seconds(self):
        """
        Returns the runtime duration of the video stream as a floating point number of seconds.
        Returns 0.0 if not a video stream.
        """
        f=None
        if self.is_video or self.is_audio:
            if self.__dict__['_duration']:
                try:
                    f=float(self.__dict__['_duration'])
                except ValueError:
                    raise FFProbeException("None numeric duration")
        return f

    @property
    def language(self):
        """
        Returns language tag of stream. e.g. eng
        """
        lang=None
        if self.__dict__['_TAG:language']:
            lang=self.__dict__['_TAG:language']
        return lang

    @property
    def bitrate(self):
        """
        Returns bitrate as an integer in bps
        """
        b=None
        if self.__dict__['_bit_rate']:
            try:
                b=int(self.__dict__['_bit_rate'])
            except ValueError:
                raise FFProbeException("None integer bitrate")
        return b
