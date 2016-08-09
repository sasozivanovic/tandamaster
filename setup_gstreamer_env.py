import os
os.environ['GSTREAMER_1_0_ROOT_X86'] = os.getcwd()
os.environ['GST_PLUGIN_PATH_1_0'] = os.path.join(os.getcwd(), 'gst_plugins')
