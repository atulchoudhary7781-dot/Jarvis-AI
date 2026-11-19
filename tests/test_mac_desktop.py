"""macOS safety logic tested using mocks; does not exercise a real Mac."""
import unittest
from unittest.mock import patch, MagicMock
from hologram import desktop

class MacBrokerTests(unittest.TestCase):
    def test_platform_allowlist_and_single_use(self):
        sent = []
        s = desktop.DesktopSession(allowed_apps=desktop.MAC_APPS, ask=lambda _: True, launch=sent.append)
        for name in ('paint', 'notepad', '/Applications/Terminal.app', 'terminal', 'calculator;whoami'):
            self.assertFalse(s.approve(name)['ok'])
        p = s.approve('textedit')['permit']
        self.assertFalse(s.commit('calculator',p)['ok'])
        p = s.approve('calculator')['permit']
        self.assertTrue(s.commit('calculator',p)['ok'])
        self.assertFalse(s.commit('calculator',p)['ok'])
        self.assertEqual(sent,['calculator'])
    @patch('hologram.desktop.sys.platform', 'darwin')
    @patch('hologram.desktop.subprocess.run')
    def test_dialog_and_fixed_launch(self, run):
        run.return_value = MagicMock(returncode=0,stdout='Open\n')
        self.assertTrue(desktop._ask('calculator'))
        args,kw=run.call_args
        self.assertEqual(args[0][:2],['/usr/bin/osascript','-e'])
        self.assertIn('default button "Cancel"',args[0][2])
        run.return_value=MagicMock(returncode=0,stdout='Cancel\n')
        self.assertFalse(desktop._ask('calculator'))
        with patch('pathlib.Path.is_dir',return_value=True):
            desktop._launch('textedit')
        args,kw=run.call_args
        self.assertEqual(args[0],['/usr/bin/open','-a','/System/Applications/TextEdit.app'])
        self.assertFalse(kw['shell'])
    @patch('hologram.desktop.sys.platform', 'darwin')
    @patch('hologram.desktop.os.geteuid',return_value=0)
    def test_root_denied(self,_):
        with self.assertRaises(ValueError): desktop.new_session()

if __name__=='__main__': unittest.main()
