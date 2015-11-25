import pyglet
from pyglet.window import key as keysym
from pyglet.gl import glTexParameteri, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_NEAREST
from vi3o.image import ptpscale
import numpy as np

class DebugViewer(object):
    paused = False
    step_counter = 0
    zoom = 1.0
    mouse_x = mouse_y = 0
    scroll = [0, 0]
    named_viewers =  {}

    def __init__(self, name='Video'):
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

    def dispatch_events(self):
        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.dispatch_event('on_draw')

    def dispatch_event(self, *e):
        for window in pyglet.app.windows:
            window.dispatch_event(*e)

    def _inc_fcnt(self):
        self.fcnt += 1

    def view(self, img, scale=False, intensity=None):
        self._inc_fcnt()
        self.window.set_caption(self.name + ' - %d' % self.fcnt)
        resize = self.image is None
        if intensity is None:
            intensity = img

        if scale:
            img = ptpscale(img)

        if img.dtype != 'B':
            img = np.minimum(np.maximum(img, 0), 255).astype('B')

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
            self.dispatch_events()
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
                self.label.text = 'x: %4d   y: %4d   I: %s' % (x, y, self.intensity[y, x])
            else:
                self.label.text = ''
        self.label.draw()

        self.window.flip()

    def on_key_press(self, key, modifiers):
        if key == keysym.Q or key == keysym.ESCAPE:
            exit(0)
        elif key == keysym.SPACE:
            DebugViewer.paused = not DebugViewer.paused
        elif key == keysym.ENTER:
            DebugViewer.step_counter += 1
        elif key == keysym.F:
            self.fullscreen = not self.fullscreen
            self.window.set_fullscreen(self.fullscreen)
        elif key == keysym.Z:
            DebugViewer.zoom = 1.0
            DebugViewer.scroll = [0, 0]
            self.dispatch_event('on_resize', self.window.width, self.window.height)
        elif key == keysym.D:
            import pdb; pdb.set_trace()


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
        self.dispatch_event('on_resize', self.window.width, self.window.height)
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
            print DebugViewer.mouse_x, DebugViewer.mouse_y


def view(img, name='Default', scale=False):
    if name not in DebugViewer.named_viewers:
        DebugViewer.named_viewers[name] = DebugViewer(name)
    DebugViewer.named_viewers[name].view(img, scale)

def viewsc(img, name='Default'):
    view(img, name, True)

if __name__ == '__main__':
    from vi3o.mkv import Mkv
    viewer = DebugViewer()

    for img in Mkv('/home/hakan/workspace/apps/hakan/pricertag/at_pricer/cam4.mkv', grey=True):
        viewer.view(img)

