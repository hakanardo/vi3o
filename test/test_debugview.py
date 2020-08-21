import numpy as np
import pytest
import os

def keep_state(func):
    def inner():
        from vi3o.debugview import DebugViewer
        DebugViewer.image_array_aspect_ratio = 16/9
        func()
        for name in list(DebugViewer.named_viewers.keys()):
            del DebugViewer.named_viewers[name]
    return inner

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_default_viewer_default_is_16_9():
    """Test exactly 16:9 aspect ratio
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(3, 16), dtype=np.uint8)
    img_2 = np.ones(shape=(3, 16), dtype=np.uint8) * 128
    img_3 = np.ones(shape=(3, 16), dtype=np.uint8) * 255

    flipp()
    view(img_1)
    view(img_2)
    view(img_3)
    flipp()

    assert DebugViewer.named_viewers["Default"].image.width == 16
    assert DebugViewer.named_viewers["Default"].image.height == 9

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_default_viewer_default_is_16_9_approx_wide():
    """Test approimatelly 16:9 aspect ratio
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(4, 16), dtype=np.uint8)
    img_2 = np.ones(shape=(4, 16), dtype=np.uint8) * 128
    img_3 = np.ones(shape=(4, 16), dtype=np.uint8) * 255

    flipp()
    view(img_1)
    view(img_2)
    view(img_3)
    flipp()

    assert DebugViewer.named_viewers["Default"].image.width == 32
    assert DebugViewer.named_viewers["Default"].image.height == 8

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_default_viewer_default_is_16_9_approx_narrow():
    """Test approimatelly 16:9 aspect ratio
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(9, 5), dtype=np.uint8)
    img_2 = np.ones(shape=(9, 5), dtype=np.uint8) * 128
    img_3 = np.ones(shape=(9, 5), dtype=np.uint8) * 255

    flipp()
    view(img_1)
    view(img_2)
    view(img_3)
    flipp()

    assert DebugViewer.named_viewers["Default"].image.width == 15
    assert DebugViewer.named_viewers["Default"].image.height == 9

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_default_viewer_1_1_vertical():
    """Test exactly 1:1 aspect ratio stacked horizontally
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(3, 9), dtype=np.uint8)
    img_2 = np.ones(shape=(3, 9), dtype=np.uint8) * 128
    img_3 = np.ones(shape=(3, 9), dtype=np.uint8) * 255

    flipp()
    view(img_1)
    view(img_2)
    view(img_3)
    flipp(aspect_ratio=1)

    assert DebugViewer.named_viewers["Default"].image.width == 9
    assert DebugViewer.named_viewers["Default"].image.height == 9

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_default_viewer_1_1_horizontal():
    """Test exactly 1:1 aspect ratio stacked vertically
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(9, 3), dtype=np.uint8)
    img_2 = np.ones(shape=(9, 3), dtype=np.uint8) * 128
    img_3 = np.ones(shape=(9, 3), dtype=np.uint8) * 255

    flipp()
    view(img_1)
    view(img_2)
    view(img_3)
    flipp(aspect_ratio=1)

    assert DebugViewer.named_viewers["Default"].image.width == 9
    assert DebugViewer.named_viewers["Default"].image.height == 9

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_default_viewer_infinite_horizontal():
    """Test infinite horizontal stacking, this is the legacy default
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(1, 10), dtype=np.uint8)
    img_2 = np.ones(shape=(1, 10), dtype=np.uint8) * 128
    img_3 = np.ones(shape=(1, 10), dtype=np.uint8) * 255

    flipp()
    view(img_1)
    view(img_2)
    view(img_3)
    flipp(aspect_ratio=float("inf"))

    assert DebugViewer.named_viewers["Default"].image.width == 30
    assert DebugViewer.named_viewers["Default"].image.height == 1

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_default_viewer_infinite_vertical():
    """Test infinite horizontal stacking, this is the legacy default
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(10, 1), dtype=np.uint8)
    img_2 = np.ones(shape=(10, 1), dtype=np.uint8) * 128
    img_3 = np.ones(shape=(10, 1), dtype=np.uint8) * 255

    flipp()
    view(img_1)
    view(img_2)
    view(img_3)
    flipp(aspect_ratio=0)

    assert DebugViewer.named_viewers["Default"].image.width == 1
    assert DebugViewer.named_viewers["Default"].image.height == 30

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_single_image_narrow():
    """Test flipp with only one image narrower than 16:9
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(10, 5), dtype=np.uint8)

    flipp()
    view(img_1)
    flipp()

    assert DebugViewer.named_viewers["Default"].image.width == 5
    assert DebugViewer.named_viewers["Default"].image.height == 10

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_flipp_aspect_ratio_single_image_wide():
    """Test flipp with only one image wider than 16:9
    """
    from vi3o import view, flipp
    from vi3o.debugview import DebugViewer

    img_1 = np.zeros(shape=(5, 10), dtype=np.uint8)

    flipp()
    view(img_1)
    flipp()

    assert DebugViewer.named_viewers["Default"].image.width == 10
    assert DebugViewer.named_viewers["Default"].image.height == 5

@pytest.mark.skipif(os.getenv("HEADLESS", False), reason="Can't test debugview when headless")
@keep_state
def test_no_default_instance_left():
    """Make sure the other test methods cleans up
    """
    from vi3o.debugview import DebugViewer
    assert not len(DebugViewer.named_viewers)

if __name__ == "__main__":
    from vi3o.debugview import DebugViewer
    DebugViewer.paused = True

    test_flipp_aspect_ratio_default_viewer_default_is_16_9_approx_narrow()
    test_flipp_aspect_ratio_default_viewer_default_is_16_9_approx_wide()
    test_flipp_aspect_ratio_default_viewer_1_1_horizontal()
    test_flipp_aspect_ratio_default_viewer_1_1_vertical()
    test_flipp_aspect_ratio_default_viewer_infinite_horizontal()
    test_flipp_aspect_ratio_default_viewer_infinite_vertical()
    test_flipp_aspect_ratio_single_image_narrow()
    test_flipp_aspect_ratio_single_image_wide()
    test_flipp_aspect_ratio_default_viewer_default_is_16_9()
    test_no_default_instance_left()
