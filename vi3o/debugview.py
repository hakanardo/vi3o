from threading import RLock

import pyglet
from pyglet.window import key as keysym
from pyglet.gl import glTexParameteri, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_NEAREST
from vi3o.image import ptpscale
import numpy as np

global_pyglet_lock = RLock()

class DebugViewer(object):
    paused = False
    step_counter = 0
    zoom = 1.0
    mouse_x = mouse_y = 0
    scroll = [0, 0]
    named_viewers =  {}

    def __init__(self, name='Video'):
        with global_pyglet_lock:
            self.window = pyglet.window.Window(resizable=True, caption=name)
            self.name = name
            self.fcnt = 0
            for name in dir(self):
                if name[:3] == 'on_':
                    self.window.event(getattr(self, name))
            self.mystep = DebugViewer.step_counter
            self.fullscreen = False
            self.image = None
            self.label = pyglet.text.Label('Hello, world',
                              font_name='Times New Roman',
                              font_size=16,
                              x=10, y=0,
                              anchor_x='left', anchor_y='bottom')
            self.label.set_style('background_color', (0,0,0,255))
            self.autoflipp = True
            self.original_image_array = None
            self.force_scale = False
            self.prev_image_shape = None

    def _dispatch_events(self):
        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.dispatch_event('on_draw')

    def _dispatch_event(self, *e):
        for window in pyglet.app.windows:
            window.dispatch_event(*e)

    def _inc_fcnt(self):
        self.fcnt += 1

    def view(self, img, scale=False, intensity=None, pause=None):
        with global_pyglet_lock:
            if img.dtype == 'bool':
                img = img.astype('B')
            if intensity is None:
                intensity = img
            if scale:
                img = ptpscale(img)
            if img.dtype != 'B':
                img = np.minimum(np.maximum(img, 0), 255).astype('B')

            if pause is not None:
                DebugViewer.paused = pause

            if self.autoflipp:
                self.image_array = [(img, intensity)]
                self._inc_fcnt()
                self._view_image_array()
            else:
                self.image_array.append((img, intensity))

    def flipp(self, pause=None):
        with global_pyglet_lock:
            if pause is not None:
                DebugViewer.paused = pause
            if not self.autoflipp:
                self._inc_fcnt()
                self._view_image_array()
            else:
                self.image = None
            self.autoflipp = False
            self.image_array = []


    def _pad_height(self, img, h):
        extra = h - img.shape[0]
        assert extra >= 0
        if extra == 0:
            return img
        top = extra // 2
        shape = list(img.shape[:2])
        shape[0]  += extra
        res = np.zeros(shape, img.dtype)
        res[top:top+img.shape[0]] = img
        return res

    def _stack(self, image_array):
        if max(len(img.shape) for img in image_array) == 3:
            images = [img if len(img.shape) == 3 else np.stack([img, img, img], 2)
                      for img in image_array]
        else:
            images = image_array
        h = max(img.shape[0] for img in image_array)
        images = [self._pad_height(img, h) for img in images]
        return np.hstack(images)

    def _view_image_array(self):

        if self.force_scale:
            self.original_image_array = self.image_array[:]
            for i in range(len(self.image_array)):
                img, intensity = self.image_array[i]
                img = ptpscale(intensity)
                img = np.minimum(np.maximum(img, 0), 255).astype('B')
                self.image_array[i] = (img, intensity)
        else:
            self.original_image_array = None

        self.window.set_caption(self.name + ' - %d' % self.fcnt)


        img = self._stack([img for img, _ in self.image_array])
        intensity = self._stack([ii for _, ii in self.image_array])
        self.color_mask = np.hstack([len(ii.shape)==3] * ii.shape[1]
                                    for _, ii in self.image_array)
        # FIXME: split image_array

        if self.image is None:
            resize = True
        else:
            resize = img.shape != self.prev_image_shape
        self.prev_image_shape = img.shape

        if len(img.shape) == 3:
            f = 'RGB'
            pitch = -img.shape[1] * 3
        else:
            f = 'I'
            pitch = -img.shape[1]
        self.image = pyglet.image.ImageData(img.shape[1], img.shape[0], f, img.tostring(), pitch)

        glTexParameteri(self.image.texture.target,
            GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(self.image.texture.target,
            GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        if resize:
            self.on_resize(self.window.width, self.window.height)

        self.intensity = intensity
        while True:
            self._dispatch_events()
            if not DebugViewer.paused:
                self.mystep = DebugViewer.step_counter
                break
            elif self.mystep < DebugViewer.step_counter:
                self.mystep += 1
                break

    def on_draw(self):
        self.window.clear()
        if self.image:
            self.image.blit(self.offset[0] + self.scroll[0], self.offset[1] + self.scroll[1], 0,
                            self.scaled_size[0], self.scaled_size[1])
            x, y = DebugViewer.mouse_x, DebugViewer.mouse_y
            if 0 <= x < self.intensity.shape[1] and 0 <= y < self.intensity.shape[0]:
                ii = self.intensity[y, x]
                if not self.color_mask[x] and len(ii.shape) > 0:
                    ii = ii[0]
                self.label.text = 'x: %4d   y: %4d   I: %s' % (x, y, ii)
            else:
                self.label.text = ''
        self.label.draw()

        self.window.flip()

    # Keys not repeated when held down
    def on_key_press(self, key, modifiers):
        if key == keysym.Q or key == keysym.ESCAPE:
            exit(0)
        elif key == keysym.F:
            self.fullscreen = not self.fullscreen
            self.window.set_fullscreen(self.fullscreen)
        elif key == keysym.Z:
            DebugViewer.zoom = 1.0
            DebugViewer.scroll = [0, 0]
            self._dispatch_event('on_resize', self.window.width, self.window.height)
        elif key == keysym.S:
            if self.force_scale:
                assert self.original_image_array is not None
                self.image_array = self.original_image_array
                self.force_scale = False
            else:
                self.force_scale = True
            self._view_image_array()
        elif key == keysym.D:
            import pdb; pdb.set_trace()

    # Keys repeated when held down
    def on_text(self, char):
        if char == " ":
            DebugViewer.paused = not DebugViewer.paused
        elif char in "\r\n":
            DebugViewer.step_counter += 1

    def on_mouse_motion(self, x, y, dx=None, dy=None):
        x = int((x - self.offset[0] - self.scroll[0]) / self.scale)
        y = self.image.height - int((y - self.offset[1] - self.scroll[1]) / self.scale) - 1
        DebugViewer.mouse_x, DebugViewer.mouse_y = x, y

    def on_resize(self, winw, winh):
        if self.image:
            lh = self.label.content_height
            self.scale = sc = min(float(winw) / self.image.width,
                                  float(winh - lh) / self.image.height) * self.zoom
            w, h = int(sc * self.image.width), int(sc * self.image.height)
            self.offset = (self.window.width - w) / 2, (self.window.height - lh - h) / 2 + lh
            self.scaled_size = w, h

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.on_mouse_motion(x, y)
        prex, prey = DebugViewer.mouse_x, DebugViewer.mouse_y
        DebugViewer.zoom *= 1.25 ** scroll_y
        self._dispatch_event('on_resize', self.window.width, self.window.height)
        self.on_mouse_motion(x, y)
        self.scroll[0] += (DebugViewer.mouse_x - prex) * self.scale
        self.scroll[1] -= (DebugViewer.mouse_y - prey) * self.scale
        self.on_mouse_motion(x, y)
        self.clicking = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        DebugViewer.scroll[0] += dx
        DebugViewer.scroll[1] += dy
        self.clicking = False

    def on_mouse_press(self, x, y, button, modifiers):
        self.clicking = True

    def on_mouse_release(self, x, y, button, modifiers):
        if self.clicking:
            print(DebugViewer.mouse_x, DebugViewer.mouse_y)

if __name__ == '__main__':
    from vi3o import Video, view
    import sys

    if len(sys.argv) < 2:
        print "Usage: python -mvi3o.debugview <video file>"
        exit(-1)

    for fn in sys.argv[1:]:
        if fn.split('.')[-1] in ('mkv', 'mjpg'):
            for img in Video(sys.argv[1]):
                view(img)
        else:
            from vi3o.image import imread, imshow
            imshow(imread(fn))