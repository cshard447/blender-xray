import unittest
import addon_utils
import io
import inspect
import os
import shutil
import sys
import tempfile
import bmesh
import bpy
from io_scene_xray.plugin import TestReadyOperator


class XRayTestCase(unittest.TestCase):
    blend_file = None
    __save_test_data = '--save-test-data' in sys.argv
    __tmp_base = os.path.join(tempfile.gettempdir(), 'io_scene_xray-tests')
    __tmp = __tmp_base + '/out'
    _reports = []

    @classmethod
    def relpath(cls, path=None):
        result = os.path.dirname(inspect.getfile(cls))
        if path is not None:
            result = os.path.join(result, path)
        return result

    @classmethod
    def outpath(cls, path=''):
        if not os.path.exists(cls.__tmp):
            os.makedirs(cls.__tmp)
        return os.path.join(cls.__tmp, path)

    def setUp(self):
        self._reports = []
        if self.blend_file:
            bpy.ops.wm.open_mainfile(filepath=self.relpath(self.blend_file))
        else:
            bpy.ops.wm.read_homefile()
        addon_utils.enable('io_scene_xray', default_set=True)
        from io_scene_xray import plugin
        plugin.load_post(None)
        self.__prev_report_catcher = TestReadyOperator.report_catcher
        TestReadyOperator.report_catcher = lambda op, type, message: self._reports.append((type, message))

    def tearDown(self):
        TestReadyOperator.report_catcher = self.__prev_report_catcher
        if os.path.exists(self.__tmp):
            if self.__save_test_data:
                bpy.ops.wm.save_mainfile(filepath=os.path.join(self.__tmp, 'result.blend'))
                new_path = os.path.join(self.__tmp_base, self.__class__.__name__, self._testMethodName)
                os.renames(self.__tmp, new_path)
            else:
                shutil.rmtree(self.__tmp)
        addon_utils.disable('io_scene_xray')

    def assertFileExists(self, path, allow_empty=False, msg=None):
        if not os.path.isfile(path):
            self.fail(self._formatMessage(msg, 'file {} is not exists'.format(path)))
        if (not allow_empty) and (os.path.getsize(path) == 0):
            self.fail(self._formatMessage(msg, 'file {} is empty'.format(path)))

    def assertOutputFiles(self, expected):
        tmp = XRayTestCase.__tmp

        for path in expected:
            self.assertFileExists(os.path.join(tmp, path))

        def scan_dir(files, path=''):
            for p in os.listdir(path):
                pp = os.path.join(path, p)
                if os.path.isdir(pp):
                    scan_dir(files, pp)
                else:
                    files.add(pp[len(tmp) + 1:])

        existing = set()
        scan_dir(existing, tmp)
        orphaned = existing - expected
        if orphaned:
            self.fail(self._formatMessage(None, 'files {} orphaned'.format(orphaned)))

    def assertFileContains(self, file_path, re_message=None):
        full_path = os.path.join(XRayTestCase.__tmp, file_path)
        content = ''
        with io.open(full_path, 'rb') as f:
            content = f.read()
        match = re_message.match(content.replace(b'\x00', b''))
        if match is not None:
            raise self.fail('Cannot match the \'{}\' file content with \'{}\''
                            .format(file_path, re_message))

    def _findReport(self, type=None, re_message=None):
        for r in self._reports:
            if (type is not None) and (type not in r[0]):
                continue
            if re_message is None:
                continue
            m = re_message.match(r[1])
            if m is not None:
                return m

    def assertReportsContains(self, type=None, re_message=None):
        r = self._findReport(type, re_message)
        if r is not None:
            return r
        raise self.fail('Cannot find report with: type={}, message={} in reports: {}'.format(type, re_message, self._reports))

    def assertReportsNotContains(self, type=None, re_message=None):
        r = self._findReport(type, re_message)
        if r is None:
            return
        raise self.fail('Found report with: type={}, message={}: {}'.format(type, re_message, r))


def create_bmesh(vertexes, indexes):
    bm = bmesh.new()
    verts = [bm.verts.new(v) for v in vertexes]
    for ii in indexes:
        bm.faces.new((verts[i] for i in ii))
    bm.loops.layers.uv.new('uv')
    return bm


def create_object(bm):
    mesh = bpy.data.meshes.new('test')
    bm.to_mesh(mesh)
    mat = bpy.data.materials.new('mat')
    mesh.materials.append(mat)
    obj = bpy.data.objects.new('test', mesh)
    bpy.context.scene.objects.link(obj)
    return obj
