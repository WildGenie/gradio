from re import sub
import unittest
import gradio as gr
import PIL
import numpy as np
import pandas
from pydub import AudioSegment
import os
import tempfile
import json


os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"


class InputComponent(unittest.TestCase):
    def test_as_component(self):
        input = gr.inputs.InputComponent(label="Test Input")
        self.assertEqual(input.preprocess("Hello World!"), "Hello World!")
        self.assertEqual(input.preprocess_example(["1", "2", "3"]), ["1", "2", "3"])
        self.assertEqual(input.serialize(1, True), 1)
        self.assertEqual(input.set_interpret_parameters(), input)
        self.assertIsNone(input.get_interpretation_neighbors("Hi!"))
        self.assertIsNone(input.get_interpretation_scores("Hi!", [], []))
        self.assertIsNone(input.generate_sample())


class TestTextbox(unittest.TestCase):
    def test_as_component(self):
        text_input = gr.inputs.Textbox()
        self.assertEqual(text_input.preprocess("Hello World!"), "Hello World!")
        self.assertEqual(text_input.preprocess_example("Hello World!"), "Hello World!")
        self.assertEqual(text_input.serialize("Hello World!", True), "Hello World!")
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = text_input.save_flagged(tmpdirname, "text_input", "Hello World!", None)
            self.assertEqual(to_save, "Hello World!")
            restored = text_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, "Hello World!")

        with self.assertWarns(DeprecationWarning):
            numeric_text_input = gr.inputs.Textbox(type="number")
        self.assertEqual(numeric_text_input.preprocess("2"), 2.0)
        with self.assertRaises(ValueError):
            wrong_type = gr.inputs.Textbox(type="unknown")
            wrong_type.preprocess(0)

        self.assertEqual(text_input.tokenize("Hello World! Gradio speaking."), (
            ['Hello', 'World!', 'Gradio', 'speaking.'],
            ['World! Gradio speaking.', 'Hello Gradio speaking.', 'Hello World! speaking.', 'Hello World! Gradio'],
            None))
        text_input.interpretation_replacement = "unknown"
        self.assertEqual(text_input.tokenize("Hello World! Gradio speaking."), (
            ['Hello', 'World!', 'Gradio', 'speaking.'],
            ['unknown World! Gradio speaking.', 'Hello unknown Gradio speaking.', 'Hello World! unknown speaking.',
             'Hello World! Gradio unknown'], None))

        self.assertIsInstance(text_input.generate_sample(), str)

    def test_in_interface(self):
        iface = gr.Interface(lambda x: x[::-1], "textbox", "textbox")
        self.assertEqual(iface.process(["Hello"])[0], ["olleH"])
        iface = gr.Interface(lambda sentence: max([len(word) for word in sentence.split()]), gr.inputs.Textbox(),
                             gr.outputs.Textbox(), interpretation="default")
        scores, alternative_outputs = iface.interpret(["Return the length of the longest word in this sentence"])
        self.assertEqual(scores, [[('Return', 0.0), (' ', 0), ('the', 0.0), (' ', 0), ('length', 0.0), (' ', 0),
                                   ('of', 0.0), (' ', 0), ('the', 0.0), (' ', 0), ('longest', 0.0), (' ', 0),
                                   ('word', 0.0), (' ', 0), ('in', 0.0), (' ', 0), ('this', 0.0), (' ', 0),
                                   ('sentence', 1.0), (' ', 0)]])
        self.assertEqual(alternative_outputs, [[['8'], ['8'], ['8'], ['8'], ['8'], ['8'], ['8'], ['8'], ['8'], ['7']]])


class TestNumber(unittest.TestCase):
    def test_as_component(self):
        numeric_input = gr.inputs.Number()
        self.assertEqual(numeric_input.preprocess(3), 3.0)
        self.assertEqual(numeric_input.preprocess_example(3), 3)
        self.assertEqual(numeric_input.serialize(3, True), 3)
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = numeric_input.save_flagged(tmpdirname, "numeric_input", 3, None)
            self.assertEqual(to_save, 3)
            restored = numeric_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, 3)
        self.assertIsInstance(numeric_input.generate_sample(), float)
        numeric_input.set_interpret_parameters(steps=3, delta=1, delta_type="absolute")
        self.assertEqual(numeric_input.get_interpretation_neighbors(1), ([-2.0, -1.0, 0.0, 2.0, 3.0, 4.0], {}))
        numeric_input.set_interpret_parameters(steps=3, delta=1, delta_type="percent")
        self.assertEqual(numeric_input.get_interpretation_neighbors(1), ([0.97, 0.98, 0.99, 1.01, 1.02, 1.03], {}))

    def test_in_interface(self):
        iface = gr.Interface(lambda x: x**2, "number", "textbox")
        self.assertEqual(iface.process([2])[0], ['4.0'])
        iface = gr.Interface(lambda x: x**2, "number", "textbox", interpretation="default")
        scores, alternative_outputs = iface.interpret([2])
        self.assertEqual(scores, [[(1.94, -0.23640000000000017), (1.96, -0.15840000000000032),
                                    (1.98, -0.07960000000000012), [2, None], (2.02, 0.08040000000000003),
                                    (2.04, 0.16159999999999997), (2.06, 0.24359999999999982)]])
        self.assertEqual(alternative_outputs, [[['3.7636'], ['3.8415999999999997'], ['3.9204'], ['4.0804'], ['4.1616'],
                                                ['4.2436']]])


class TestSlider(unittest.TestCase):
    def test_as_component(self):
        slider_input = gr.inputs.Slider()
        self.assertEqual(slider_input.preprocess(3.0), 3.0)
        self.assertEqual(slider_input.preprocess_example(3), 3)
        self.assertEqual(slider_input.serialize(3, True), 3)
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = slider_input.save_flagged(tmpdirname, "slider_input", 3, None)
            self.assertEqual(to_save, 3)
            restored = slider_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, 3)

        self.assertIsInstance(slider_input.generate_sample(), int)
        slider_input = gr.inputs.Slider(minimum=10, maximum=20, step=1, default=15, label="Slide Your Input")
        self.assertEqual(slider_input.get_template_context(), {
            'minimum': 10,
            'maximum': 20,
            'step': 1,
            'default': 15,
            'name': 'slider',
            'label': 'Slide Your Input'
        })

    def test_in_interface(self):
        iface = gr.Interface(lambda x: x**2, "slider", "textbox")
        self.assertEqual(iface.process([2])[0], ['4'])
        iface = gr.Interface(lambda x: x**2, "slider", "textbox", interpretation="default")
        scores, alternative_outputs = iface.interpret([2])
        self.assertEqual(scores, [[-4.0, 200.08163265306123, 812.3265306122449, 1832.7346938775513, 3261.3061224489797,
                                   5098.040816326531, 7342.938775510205, 9996.0]])
        self.assertEqual(alternative_outputs, [[['0.0'], ['204.08163265306123'], ['816.3265306122449'],
                                                ['1836.7346938775513'], ['3265.3061224489797'], ['5102.040816326531'],
                                                ['7346.938775510205'], ['10000.0']]])


class TestCheckbox(unittest.TestCase):
    def test_as_component(self):
        bool_input = gr.inputs.Checkbox()
        self.assertEqual(bool_input.preprocess(True), True)
        self.assertEqual(bool_input.preprocess_example(True), True)
        self.assertEqual(bool_input.serialize(True, True), True)
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = bool_input.save_flagged(tmpdirname, "bool_input", True, None)
            self.assertEqual(to_save, True)
            restored = bool_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, True)
        self.assertIsInstance(bool_input.generate_sample(), bool)
        bool_input = gr.inputs.Checkbox(default=True, label="Check Your Input")
        self.assertEqual(bool_input.get_template_context(), {
            'default': True,
            'name': 'checkbox',
            'label': 'Check Your Input'
        })

    def test_in_interface(self):
        iface = gr.Interface(lambda x: 1 if x else 0, "checkbox", "textbox")
        self.assertEqual(iface.process([True])[0], ['1'])
        iface = gr.Interface(lambda x: 1 if x else 0, "checkbox", "textbox", interpretation="default")
        scores, alternative_outputs = iface.interpret([False])
        self.assertEqual(scores, [(None, 1.0)])
        self.assertEqual(alternative_outputs, [[['1']]])
        scores, alternative_outputs = iface.interpret([True])
        self.assertEqual(scores, [(-1.0, None)])
        self.assertEqual(alternative_outputs, [[['0']]])


class TestCheckboxGroup(unittest.TestCase):
    def test_as_component(self):
        checkboxes_input = gr.inputs.CheckboxGroup(["a", "b", "c"])
        self.assertEqual(checkboxes_input.preprocess(["a", "c"]), ["a", "c"])
        self.assertEqual(checkboxes_input.preprocess_example(["a", "c"]), ["a", "c"])
        self.assertEqual(checkboxes_input.serialize(["a", "c"], True), ["a", "c"])
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = checkboxes_input.save_flagged(tmpdirname, "checkboxes_input", ["a", "c"], None)
            self.assertEqual(to_save, '["a", "c"]')
            restored = checkboxes_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, ["a", "c"])
        self.assertIsInstance(checkboxes_input.generate_sample(), list)
        checkboxes_input = gr.inputs.CheckboxGroup(choices=["a", "b", "c"], default=["a", "c"],
                                                   label="Check Your Inputs")
        self.assertEqual(checkboxes_input.get_template_context(), {
            'choices': ['a', 'b', 'c'],
             'default': ['a', 'c'],
             'name': 'checkboxgroup',
             'label': 'Check Your Inputs'
        })
        with self.assertRaises(ValueError):
            wrong_type = gr.inputs.CheckboxGroup(["a"], type="unknown")
            wrong_type.preprocess(0)

    def test_in_interface(self):
        checkboxes_input = gr.inputs.CheckboxGroup(["a", "b", "c"])
        iface = gr.Interface(lambda x: "|".join(x), checkboxes_input, "textbox")
        self.assertEqual(iface.process([["a", "c"]])[0], ["a|c"])
        self.assertEqual(iface.process([[]])[0], [""])
        checkboxes_input = gr.inputs.CheckboxGroup(["a", "b", "c"], type="index")
        iface = gr.Interface(lambda x: "|".join(map(str, x)), checkboxes_input, "textbox", interpretation="default")
        self.assertEqual(iface.process([["a", "c"]])[0], ["0|2"])
        scores, alternative_outputs = iface.interpret([["a", "c"]])
        self.assertEqual(scores, [[[-1, None], [None, -1], [-1, None]]])
        self.assertEqual(alternative_outputs, [[['2'], ['0|2|1'], ['0']]])


class TestRadio(unittest.TestCase):
    def test_as_component(self):
        radio_input = gr.inputs.Radio(["a", "b", "c"])
        self.assertEqual(radio_input.preprocess("c"), "c")
        self.assertEqual(radio_input.preprocess_example("a"), "a")
        self.assertEqual(radio_input.serialize("a", True), "a")
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = radio_input.save_flagged(tmpdirname, "radio_input", "a", None)
            self.assertEqual(to_save, 'a')
            restored = radio_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, "a")
        self.assertIsInstance(radio_input.generate_sample(), str)
        radio_input = gr.inputs.Radio(choices=["a", "b", "c"], default="a",
                                                   label="Pick Your One Input")
        self.assertEqual(radio_input.get_template_context(), {
            'choices': ['a', 'b', 'c'],
             'default': 'a',
             'name': 'radio',
             'label': 'Pick Your One Input'
        })
        with self.assertRaises(ValueError):
            wrong_type = gr.inputs.Radio(["a","b"], type="unknown")
            wrong_type.preprocess(0)

    def test_in_interface(self):
        radio_input = gr.inputs.Radio(["a", "b", "c"])
        iface = gr.Interface(lambda x: 2 * x, radio_input, "textbox")
        self.assertEqual(iface.process(["c"])[0], ["cc"])
        radio_input = gr.inputs.Radio(["a", "b", "c"], type="index")
        iface = gr.Interface(lambda x: 2 * x, radio_input, "number", interpretation="default")
        self.assertEqual(iface.process(["c"])[0], [4])
        scores, alternative_outputs = iface.interpret(["b"])
        self.assertEqual(scores, [[-2.0, None, 2.0]])
        self.assertEqual(alternative_outputs, [[[0], [4]]])


class TestDropdown(unittest.TestCase):
    def test_as_component(self):
        dropdown_input = gr.inputs.Dropdown(["a", "b", "c"])
        self.assertEqual(dropdown_input.preprocess("c"), "c")
        self.assertEqual(dropdown_input.preprocess_example("a"), "a")
        self.assertEqual(dropdown_input.serialize("a", True), "a")
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = dropdown_input.save_flagged(tmpdirname, "dropdown_input", "a", None)
            self.assertEqual(to_save, 'a')
            restored = dropdown_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, "a")
        self.assertIsInstance(dropdown_input.generate_sample(), str)
        dropdown_input = gr.inputs.Dropdown(choices=["a", "b", "c"], default="a",
                                                   label="Drop Your Input")
        self.assertEqual(dropdown_input.get_template_context(), {
            'choices': ['a', 'b', 'c'],
            'default': 'a',
            'name': 'dropdown',
            'label': 'Drop Your Input'
        })
        with self.assertRaises(ValueError):
            wrong_type = gr.inputs.Dropdown(["a"], type="unknown")
            wrong_type.preprocess(0)

    def test_in_interface(self):
        dropdown_input = gr.inputs.Dropdown(["a", "b", "c"])
        iface = gr.Interface(lambda x: 2 * x, dropdown_input, "textbox")
        self.assertEqual(iface.process(["c"])[0], ["cc"])
        dropdown = gr.inputs.Dropdown(["a", "b", "c"], type="index")
        iface = gr.Interface(lambda x: 2 * x, dropdown, "number", interpretation="default")
        self.assertEqual(iface.process(["c"])[0], [4])
        scores, alternative_outputs = iface.interpret(["b"])
        self.assertEqual(scores, [[-2.0, None, 2.0]])
        self.assertEqual(alternative_outputs, [[[0], [4]]])


class TestImage(unittest.TestCase):
    def test_as_component(self):
        img = gr.test_data.BASE64_IMAGE
        image_input = gr.inputs.Image()
        self.assertEqual(image_input.preprocess(img).shape, (68, 61, 3))
        image_input = gr.inputs.Image(image_mode="L", shape=(25, 25))
        self.assertEqual(image_input.preprocess(img).shape, (25, 25))
        image_input = gr.inputs.Image(shape=(30, 10), type="pil")
        self.assertEqual(image_input.preprocess(img).size, (30, 10))
        self.assertEqual(image_input.preprocess_example("test/test_files/bus.png"), img)
        self.assertEqual(image_input.serialize("test/test_files/bus.png", True), img)
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = image_input.save_flagged(tmpdirname, "image_input", img, None)
            self.assertEqual("image_input/0.png", to_save)
            to_save = image_input.save_flagged(tmpdirname, "image_input", img, None)
            self.assertEqual("image_input/1.png", to_save)
            restored = image_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, "image_input/1.png")

        self.assertIsInstance(image_input.generate_sample(), str)
        image_input = gr.inputs.Image(source="upload", tool="editor", type="pil", label="Upload Your Image")
        self.assertEqual(image_input.get_template_context(), {
            'image_mode': 'RGB',
            'shape': None,
            'source': 'upload',
            'tool': 'editor',
            'optional': False,
            'name': 'image',
            'label': 'Upload Your Image'
        })
        self.assertIsNone(image_input.preprocess(None))
        image_input = gr.inputs.Image(invert_colors=True)
        self.assertIsNotNone(image_input.preprocess(img))
        image_input.preprocess(img)
        with self.assertWarns(DeprecationWarning):
            file_image = gr.inputs.Image(type="file")
            file_image.preprocess(gr.test_data.BASE64_IMAGE)
        file_image = gr.inputs.Image(type="filepath")
        self.assertIsInstance(file_image.preprocess(img), str)
        with self.assertRaises(ValueError):
            wrong_type = gr.inputs.Image(type="unknown")
            wrong_type.preprocess(img)
        with self.assertRaises(ValueError):
            wrong_type = gr.inputs.Image(type="unknown")
            wrong_type.serialize("test/test_files/bus.png", False)
        img_pil = PIL.Image.open('test/test_files/bus.png')
        image_input = gr.inputs.Image(type="numpy")
        self.assertIsInstance(image_input.serialize(img_pil, False), str)
        image_input = gr.inputs.Image(type="pil")
        self.assertIsInstance(image_input.serialize(img_pil, False), str)
        image_input = gr.inputs.Image(type="file")
        with open("test/test_files/bus.png") as f:
            self.assertEqual(image_input.serialize(f, False), img)
        image_input.shape = (30, 10)
        self.assertIsNotNone(image_input._segment_by_slic(img))

    def test_in_interface(self):
        img = gr.test_data.BASE64_IMAGE
        image_input = gr.inputs.Image()
        iface = gr.Interface(lambda x: PIL.Image.open(x).rotate(90, expand=True),
                             gr.inputs.Image(shape=(30, 10), type="file"), "image")
        output = iface.process([img])[0][0]
        self.assertEqual(gr.processing_utils.decode_base64_to_image(output).size, (10, 30))
        iface = gr.Interface(lambda x: np.sum(x), image_input, "textbox", interpretation="default")
        scores, alternative_outputs = iface.interpret([img])
        self.assertEqual(scores, gr.test_data.SUM_PIXELS_INTERPRETATION["scores"])
        self.assertEqual(alternative_outputs, gr.test_data.SUM_PIXELS_INTERPRETATION["alternative_outputs"])
        iface = gr.Interface(lambda x: np.sum(x), image_input, "label", interpretation="shap")
        scores, alternative_outputs = iface.interpret([img])
        self.assertEqual(len(scores[0]), len(gr.test_data.SUM_PIXELS_SHAP_INTERPRETATION["scores"][0]))
        self.assertEqual(len(alternative_outputs[0]),
                         len(gr.test_data.SUM_PIXELS_SHAP_INTERPRETATION["alternative_outputs"][0]))
        image_input = gr.inputs.Image(shape=(30, 10))
        iface = gr.Interface(lambda x: np.sum(x), image_input, "textbox", interpretation="default")
        self.assertIsNotNone(iface.interpret([img]))


class TestAudio(unittest.TestCase):
    def test_as_component(self):
        x_wav = gr.test_data.BASE64_AUDIO
        audio_input = gr.inputs.Audio()
        output = audio_input.preprocess(x_wav)
        self.assertEqual(output[0], 8000)
        self.assertEqual(output[1].shape, (8046,))
        self.assertEqual(audio_input.serialize("test/test_files/audio_sample.wav", True)["data"], x_wav["data"])
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = audio_input.save_flagged(tmpdirname, "audio_input", x_wav, None)
            self.assertEqual("audio_input/0.wav", to_save)
            to_save = audio_input.save_flagged(tmpdirname, "audio_input", x_wav, None)
            self.assertEqual("audio_input/1.wav", to_save)
            restored = audio_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, "audio_input/1.wav")

        self.assertIsInstance(audio_input.generate_sample(), dict)
        audio_input = gr.inputs.Audio(label="Upload Your Audio")
        self.assertEqual(audio_input.get_template_context(), {
            'source': 'upload',
             'optional': False,
             'name': 'audio',
             'label': 'Upload Your Audio'
        })
        self.assertIsNone(audio_input.preprocess(None))
        x_wav["is_example"] = True
        x_wav["crop_min"], x_wav["crop_max"] = 1, 4
        self.assertIsNotNone(audio_input.preprocess(x_wav))
        with self.assertWarns(DeprecationWarning):
            audio_input = gr.inputs.Audio(type="file")
            audio_input.preprocess(x_wav)
            with open("test/test_files/audio_sample.wav") as f:
                audio_input.serialize(f, False)
        audio_input = gr.inputs.Audio(type="filepath")
        self.assertIsInstance(audio_input.preprocess(x_wav), str)
        with self.assertRaises(ValueError):
            audio_input = gr.inputs.Audio(type="unknown")
            audio_input.preprocess(x_wav)
            audio_input.serialize(x_wav, False)
        audio_input = gr.inputs.Audio(type="numpy")
        x_wav = gr.processing_utils.audio_from_file("test/test_files/audio_sample.wav")
        self.assertIsInstance(audio_input.serialize(x_wav, False), dict)


    # def test_in_interface(self):
    #     x_wav = gr.test_data.BASE64_AUDIO
    #     def max_amplitude_from_wav_file(wav_file):
    #         audio_segment = AudioSegment.from_file(wav_file.name)
    #         data = np.array(audio_segment.get_array_of_samples())
    #         return np.max(data)
    #     iface = gr.Interface(
    #         max_amplitude_from_wav_file,
    #         gr.inputs.Audio(type="file"),
    #         "number", interpretation="default")
    # # TODO(aliabd): investigate why this sometimes fails (returns 5239 or 576)        
    #     self.assertEqual(iface.process([x_wav])[0], [576])
    #     scores, alternative_outputs = iface.interpret([x_wav])
    #     self.assertEqual(scores, ... )
    #     self.assertEqual(alternative_outputs, ...)


class TestFile(unittest.TestCase):
    def test_as_component(self):
        x_file = gr.test_data.BASE64_FILE
        file_input = gr.inputs.File()
        output = file_input.preprocess(x_file)
        self.assertIsInstance(output, tempfile._TemporaryFileWrapper)
        self.assertEqual(file_input.serialize("test/test_files/sample_file.pdf", True), 'test/test_files/sample_file.pdf')
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = file_input.save_flagged(tmpdirname, "file_input", [x_file], None)
            self.assertEqual("file_input/0", to_save)
            to_save = file_input.save_flagged(tmpdirname, "file_input", [x_file], None)
            self.assertEqual("file_input/1", to_save)
            restored = file_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, "file_input/1")

        self.assertIsInstance(file_input.generate_sample(), dict)
        file_input = gr.inputs.File(label="Upload Your File")
        self.assertEqual(file_input.get_template_context(), {
            'file_count': 'single',
            'optional': False,
            'name': 'file',
            'label': 'Upload Your File'
        })
        self.assertIsNone(file_input.preprocess(None))
        x_file["is_example"] = True
        self.assertIsNotNone(file_input.preprocess(x_file))

    def test_in_interface(self):
        x_file = gr.test_data.BASE64_FILE

        def get_size_of_file(file_obj):
            return os.path.getsize(file_obj.name)
        iface = gr.Interface(
            get_size_of_file, "file", "number")
        self.assertEqual(iface.process([[x_file]])[0], [10558])


class TestDataframe(unittest.TestCase):
    def test_as_component(self):
        x_data = [["Tim", 12, False], ["Jan", 24, True]]
        dataframe_input = gr.inputs.Dataframe(headers=["Name","Age","Member"])
        output = dataframe_input.preprocess(x_data)
        self.assertEqual(output["Age"][1], 24)
        self.assertEqual(output["Member"][0], False)
        self.assertEqual(dataframe_input.preprocess_example(x_data), x_data)
        self.assertEqual(dataframe_input.serialize(x_data, True), x_data)
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = dataframe_input.save_flagged(tmpdirname, "dataframe_input", x_data, None)
            self.assertEqual(json.dumps(x_data), to_save)
            restored = dataframe_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(x_data, restored)

        self.assertIsInstance(dataframe_input.generate_sample(), list)
        dataframe_input = gr.inputs.Dataframe(headers=["Name", "Age", "Member"], label="Dataframe Input")
        self.assertEqual(dataframe_input.get_template_context(), {
            'headers': ['Name', 'Age', 'Member'],
            'datatype': 'str',
            'row_count': 3,
            'col_count': 3,
            'col_width': None,
            'default': [[None, None, None], [None, None, None], [None, None, None]],
            'name': 'dataframe',
            'label': 'Dataframe Input'
        })
        dataframe_input = gr.inputs.Dataframe()
        output = dataframe_input.preprocess(x_data)
        self.assertEqual(output[1][1], 24)
        with self.assertRaises(ValueError):
            wrong_type = gr.inputs.Dataframe(type="unknown")
            wrong_type.preprocess(x_data)

    def test_in_interface(self):
        x_data = [[1, 2, 3], [4, 5, 6]]
        iface = gr.Interface(np.max, "numpy", "number")
        self.assertEqual(iface.process([x_data])[0], [6])
        x_data = [["Tim"], ["Jon"], ["Sal"]]

        def get_last(l):
            return l[-1]
        iface = gr.Interface(get_last, "list", "text")
        self.assertEqual(iface.process([x_data])[0], ["Sal"])


class TestVideo(unittest.TestCase):
    def test_as_component(self):
        x_video = gr.test_data.BASE64_VIDEO
        video_input = gr.inputs.Video()
        output = video_input.preprocess(x_video)
        self.assertIsInstance(output, str)
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = video_input.save_flagged(tmpdirname, "video_input", x_video, None)
            self.assertEqual("video_input/0.mp4", to_save)
            to_save = video_input.save_flagged(tmpdirname, "video_input", x_video, None)
            self.assertEqual("video_input/1.mp4", to_save)
            restored = video_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(restored, "video_input/1.mp4")
        
        self.assertIsInstance(video_input.generate_sample(), dict)
        video_input = gr.inputs.Video(label="Upload Your Video")
        self.assertEqual(video_input.get_template_context(), {
            'source': 'upload',
            'optional': False,
            'name': 'video',
            'label': 'Upload Your Video'
        })
        self.assertIsNone(video_input.preprocess(None))
        x_video["is_example"] = True
        self.assertIsNotNone(video_input.preprocess(x_video))
        video_input = gr.inputs.Video(type="avi")
        # self.assertEqual(video_input.preprocess(x_video)[-3:], "avi")
        with self.assertRaises(NotImplementedError):
            video_input.serialize(x_video, True)


    def test_in_interface(self):
        x_video = gr.test_data.BASE64_VIDEO
        iface = gr.Interface(
            lambda x:x,
            "video",
            "playable_video")
        self.assertEqual(iface.process([x_video])[0][0]["data"], x_video["data"])


class TestTimeseries(unittest.TestCase):
    def test_as_component(self):
        timeseries_input = gr.inputs.Timeseries(
            x="time",
            y=["retail", "food", "other"]
        )
        x_timeseries = {"data": [[1] + [2] * len(timeseries_input.y)] * 4, "headers": [timeseries_input.x] +
                                                                                      timeseries_input.y}
        output = timeseries_input.preprocess(x_timeseries)
        self.assertIsInstance(output, pandas.core.frame.DataFrame)
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            to_save = timeseries_input.save_flagged(tmpdirname, "video_input", x_timeseries, None)
            self.assertEqual(json.dumps(x_timeseries), to_save)
            restored = timeseries_input.restore_flagged(tmpdirname, to_save, None)
            self.assertEqual(x_timeseries, restored)

        self.assertIsInstance(timeseries_input.generate_sample(), dict)
        timeseries_input = gr.inputs.Timeseries(
            x="time",
            y="retail", label="Upload Your Timeseries"
        )
        self.assertEqual(timeseries_input.get_template_context(), {
            'x': 'time',
            'y': ['retail'],
            'optional': False,
            'name': 'timeseries',
            'label': 'Upload Your Timeseries'
        })
        self.assertIsNone(timeseries_input.preprocess(None))
        x_timeseries["range"] = (0, 1)
        self.assertIsNotNone(timeseries_input.preprocess(x_timeseries))

    def test_in_interface(self):
        timeseries_input = gr.inputs.Timeseries(
            x="time",
            y=["retail", "food", "other"]
        )
        x_timeseries = {"data": [[1] + [2] * len(timeseries_input.y)] * 4, "headers": [timeseries_input.x] +
                                                                                      timeseries_input.y}
        iface = gr.Interface(
            lambda x: x,
            timeseries_input,
            "dataframe")
        self.assertEqual(iface.process([x_timeseries])[0], [{'headers': ['time', 'retail', 'food', 'other'],
                                                                 'data': [[1, 2, 2, 2], [1, 2, 2, 2], [1, 2, 2, 2],
                                                                          [1, 2, 2, 2]]}])


class TestNames(unittest.TestCase):
    # this ensures that `inputs.get_input_instance()` works correctly when instantiating from components
    def test_no_duplicate_uncased_names(self):  
        subclasses = gr.inputs.InputComponent.__subclasses__()
        unique_subclasses_uncased = set([s.__name__.lower() for s in subclasses])
        self.assertEqual(len(subclasses), len(unique_subclasses_uncased))


if __name__ == '__main__':
    unittest.main()
