import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import focus,paths
from engine.papers import create
from engine.tagger import score_text

class EngineTests(unittest.TestCase):
 def test_internal_path_rejects_escape(self):
  with self.assertRaises(paths.PathConfigurationError): paths.inside('..','outside')
 def test_focus_combines_levels_and_hashes(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); station=root/'station'; paper=root/'paper'; station.mkdir(); (paper/'01_NOTES').mkdir(parents=True)
   (station/'FOCUS.md').write_text('# comment\n- standing\n'); (paper/'01_NOTES'/'FOCUS.md').write_text('- paper\n')
   text,digest=focus.compose(station,paper,'run')
   self.assertIn('standing',text); self.assertIn('paper',text); self.assertIn('run',text); self.assertEqual(64,len(digest))
 def test_new_paper_is_portable_and_tagged(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); source=root/'Source.txt'; source.write_text('The resurrection supports hope.')
   config=root/'paths.json'; config.write_text(json.dumps({'papers_root':str(root/'papers'),'catalog_db':str(root/'catalog.sqlite')})); (root/'papers').mkdir()
   with patch.dict(os.environ,{'ONE_MENU_PATHS_FILE':str(config)}):
    destination=create(source)
   meta=json.loads((destination/'paper.json').read_text()); self.assertEqual(meta['source_hash'],(destination/'00_SOURCE'/'sha256.txt').read_text().split()[0]); self.assertIn('resurrection',meta['tags'])
 def test_local_tagger_returns_evidence(self):
  score,reason,quote=score_text('Resurrection evidence appears here.','resurrection'); self.assertGreater(score,0); self.assertIn('Resurrection',quote)

if __name__=='__main__': unittest.main()
