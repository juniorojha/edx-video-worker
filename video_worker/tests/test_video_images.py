"""
Video image generation tests.
"""
from ddt import ddt, data, unpack
from mock import patch, Mock
import os
import unittest
from PIL import Image


from video_worker import video_images

MOCK_SETTINGS = {
    'ffmpeg_compiled': 'ffmpeg',
    'val_client_id':  None,
    'val_video_images_url': 'https://www.testimg.com/update/images'
}


class MockVideo(object):
    """
    Mock VideoObject
    """
    mezz_duration = 16
    course_url = None
    val_id = None


@ddt
class VideoImagesTest(unittest.TestCase):
    """
    Video images generation test class.
    """
    def setUp(self):
        self.work_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'test_videofiles'
        )
        self.source_file = 'test.mp4'

    @data(
        {
            'duration': 10, 'positions': [1, 4, 7],
        },
        {
            'duration': 387, 'positions': [8, 122, 236],
        },
        {
            'duration': 888, 'positions': [18, 279, 540],
        }
    )
    @unpack
    def test_calculate_positions(self, duration, positions):
        """
        Verify that VideoImages.calculate_positions method works as expected.
        """
        self.assertEqual(video_images.VideoImages.calculate_positions(duration), positions)

    @unittest.skipIf(
        'TRAVIS' in os.environ and os.environ['TRAVIS'] == 'true',
        'Skipping this test on Travis CI due to unavailability of required ffmpeg version.'
    )
    def test_generate(self):
        """
        Verify that VideoImages.generate method works as expected.
        """
        images = video_images.VideoImages(
            video_object=MockVideo,
            work_dir=self.work_dir,
            source_file=self.source_file,
            jobid=101,
            settings=MOCK_SETTINGS
        ).generate()

        self.assertEqual(len(images), video_images.IMAGE_COUNT)

        for image in images:
            with Image.open(image) as img:
                self.assertEqual(img.size, (video_images.IMAGE_WIDTH, video_images.IMAGE_HEIGHT))

    @data(
        (
            ['course-v1:W3Cx+HTML5.0x+1T2017', 'course-v1:W3Cx+HTML5.0x+1T2018', 'course-v1:W3Cx+HTML5.0x+1T2019'],
            ['video-images/abc.png'],
            True,
            3
        ),
        (
            ['course-v1:W3Cx+HTML5.0x+1T2017', 'course-v1:W3Cx+HTML5.0x+1T2018'],
            ['video-images/abc.png'],
            True,
            2
        ),
        (
            [],
            ['video-images/abc.png'],
            False,
            0
        ),
    )
    @unpack
    @patch('video_worker.video_images.generate_apitoken.val_tokengen', Mock(return_value='val_api_token'))
    def test_update_val(self, course_ids, image_keys, post_called, post_call_count):
        """
        Verify that VideoImages.update_val method works as expected.
        """
        with patch('video_worker.video_images.requests.post', Mock(return_value=Mock(ok=True))) as mock_post:
            MockVideo.course_url = course_ids
            video_images.VideoImages(
                video_object=MockVideo,
                work_dir=self.work_dir,
                source_file=self.source_file,
                jobid=101,
                settings=MOCK_SETTINGS
            ).update_val(image_keys)

            self.assertEqual(mock_post.called, post_called)
            self.assertEqual(mock_post.call_count, post_call_count)
