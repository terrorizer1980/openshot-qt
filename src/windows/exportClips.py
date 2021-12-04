from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QWidget, QPushButton, QDialog
from classes.filePicker import filePicker

# _ = get_app()._tr

class clipExportWindow(QDialog):
    """A popup to export clips as mp4 files
    in a folder of the user's choosing"""
    layout = QVBoxLayout()
    fp: filePicker
    export_button: QPushButton

    # def __init__(self, parent, *args, **kwargs):
    #     super().__init__(parent)
    def __init__(self, export_clips_arg, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.export_clips = export_clips_arg
        # self.export_clips = kwargs.get("export_clips", [])
        self._create_widgets()

    def _create_widgets(self):
        #create
        self.fp = filePicker(folder_only=True, export_clips=self.export_clips)
        self.export_button = QPushButton("Export")

        self.layout.addWidget(self.fp)
        self.layout.addWidget(self.export_button)
        self.setMinimumWidth(500)
        self.setLayout(self.layout)

    def _export_button_pressed(self):
        print("BUTTON PRESSED")
        pass
        # copy export loop from export.py

    def setPath(self, p: str):
        self.fp.setPath(p)

    def exportClips(self):
        import openshot, os
        from classes import info

        title_message = ""

        def framesInClip(cl, fps):
            seconds = cl.data.get('end') - cl.data.get('start')
            return seconds * fps + 1

        self.disableControls()
        if ( not self.export_clips ):
            return
        # Init export settings
        interlacedIndex = self.cboInterlaced.currentIndex()
        video_settings = {"vformat": self.txtVideoFormat.text(),
                          "vcodec": self.txtVideoCodec.text(),
                          "fps": {"num": self.txtFrameRateNum.value(), "den": self.txtFrameRateDen.value()},
                          "width": self.txtWidth.value(),
                          "height": self.txtHeight.value(),
                          "pixel_ratio": {"num": self.txtPixelRatioNum.value(),
                                          "den": self.txtPixelRatioDen.value()},
                          "video_bitrate": int(self.convert_to_bytes(self.txtVideoBitRate.text())),
                          "start_frame": self.txtStartFrame.value(),
                          "end_frame": self.txtEndFrame.value(),
                          "interlace": interlacedIndex in [1, 2],
                          "topfirst": interlacedIndex == 1
                          }

        audio_settings = {"acodec": self.txtAudioCodec.text(),
                          "sample_rate": self.txtSampleRate.value(),
                          "channels": self.txtChannels.value(),
                          "channel_layout": self.cboChannelLayout.currentData(),
                          "audio_bitrate": int(self.convert_to_bytes(self.txtAudioBitrate.text()))
                          }
        interlacedIndex = self.cboInterlaced.currentIndex()
        video_settings = {  "vformat": self.txtVideoFormat.text(),
                            "vcodec": self.txtVideoCodec.text(),
                            "fps": { "num" : self.txtFrameRateNum.value(), "den": self.txtFrameRateDen.value()},
                            "width": self.txtWidth.value(),
                            "height": self.txtHeight.value(),
                            "pixel_ratio": {"num": self.txtPixelRatioNum.value(), "den": self.txtPixelRatioDen.value()},
                            "video_bitrate": int(self.convert_to_bytes(self.txtVideoBitRate.text())),
                            "start_frame": self.txtStartFrame.value(),
                            "end_frame": self.txtEndFrame.value(),
                            "interlace": interlacedIndex in [1, 2],
                            "topfirst": interlacedIndex == 1
                            }

        self.disableControls()
        self.exporting = True

        # Total number of frames
        fps = video_settings.get("fps").get("num") / video_settings.get("fps").get("den")
        totalFrames = 0
        currentFrame = 0
        for c in self.export_clips:
            totalFrames += framesInClip(c, fps)

        for c in self.export_clips:
            file_path = c.data.get("path")
            extension = file_path.split('.').pop()
            clip_name = c.data.get("name")
            # and end time * frames per second
            project_folder = os.path.realpath( os.path.join(info.BLENDER_PATH, "../../"))
            export_path = os.path.join(project_folder, f"{clip_name}.{extension}")
            # Get clip's name
            w = openshot.FFmpegWriter(export_path)

            export_type = self.cboExportTo.currentText()
            # Set video options
            if export_type in [_("Video & Audio"), _("Video Only"), _("Image Sequence")]:
                w.SetVideoOptions(True,
                                  video_settings.get("vcodec"),
                                  openshot.Fraction(video_settings.get("fps").get("num"),
                                                    video_settings.get("fps").get("den")),
                                  video_settings.get("width"),
                                  video_settings.get("height"),
                                  openshot.Fraction(video_settings.get("pixel_ratio").get("num"),
                                                    video_settings.get("pixel_ratio").get("den")),
                                  video_settings.get("interlace"),
                                  video_settings.get("topfirst"),
                                  video_settings.get("video_bitrate"))
            # Set audio options
            if export_type in [_("Video & Audio"), _("Audio Only")]:
                w.SetAudioOptions(True,
                                  audio_settings.get("acodec"),
                                  audio_settings.get("sample_rate"),
                                  audio_settings.get("channels"),
                                  audio_settings.get("channel_layout"),
                                  audio_settings.get("audio_bitrate"))
            w.PrepareStreams()
            w.Open()

            start_time = c.data.get("start")
            end_time = c.data.get("end")
            start_frame, end_frame = int(start_time * fps), int(end_time*fps)

            # Or a file reaer, and do the math for the first/last frame
            clip_reader = openshot.Clip(file_path)
            clip_reader.Open()

            log.info(f"Starting to write frames to {export_path}")

            for frame in range(start_frame, end_frame):
                w.WriteFrame(clip_reader.GetFrame(frame))

                # Check if we need to bail out
                if not self.exporting:
                    break
                # TODO DISPLAY COMPLETE RATIO TO PROGRESS BAR
            clip_reader.Close()
            currentFrame += 1
            format_of_progress_string = "%4." + str(digits_after_decimalpoint) + "f%% "
            self.updateProgressBar(self, title_message, 0, toatalFrames, currentFrame,
                                   format_of_progress_string)

            # Close writer
            w.Close()
            self.exporting=False
            self.cancel_button.setVisible(False)
            self.export_button.setVisible(False)

            # Reveal done button
            self.close_button.setVisible(True)
