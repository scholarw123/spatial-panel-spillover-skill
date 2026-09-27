import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
from shapely.geometry import box
from run_spatial_extensions import (
    contiguity_A_from_geometries, row_standardize, knn_A, distance_band_A,
    distance_ring_A, diagnose_W, moran_i, bivariate_moran_i, local_moran,
    PanelEngine, economic_A, decay_A, contiguity_A_from_boundary_file, lisa_map_if_boundary
)

class SpatialExtensionTests(unittest.TestCase):
    def test_queen_rook_corner(self):
        polys=[box(0,0,1,1), box(1,0,2,1), box(2,1,3,2)]
        q=contiguity_A_from_geometries(polys,'queen').astype(int).tolist()
        r=contiguity_A_from_geometries(polys,'rook').astype(int).tolist()
        self.assertEqual(q, [[0,1,0],[1,0,1],[0,1,0]])
        self.assertEqual(r, [[0,1,0],[1,0,0],[0,0,0]])
    def test_row_sum(self):
        A=np.array([[0,1,2],[1,0,0],[2,0,0]],float)
        self.assertTrue(np.allclose(row_standardize(A).sum(axis=1),1))
    def test_isolate(self):
        A=np.array([[0,1,0],[1,0,0],[0,0,0]],float)
        d=diagnose_W(A,labels=['A','B','C'])
        self.assertEqual(d['isolates'],1);self.assertEqual(d['components'],2)
    def test_distance_ring_disjoint(self):
        D=np.array([[0,100,300],[100,0,200],[300,200,0]],float)
        a=distance_ring_A(D,0,150);b=distance_ring_A(D,150,400)
        self.assertFalse(np.any((a>0)&(b>0)))
    def test_knn(self):
        D=np.array([[0,2,5],[2,0,3],[5,3,0]],float)
        A=knn_A(D,1,'union')
        self.assertTrue(np.allclose(A,A.T));self.assertTrue(np.all(np.diag(A)==0))
    def test_economic_and_decay(self):
        E,m=economic_A(np.array([1.,1.,2.]),'inverse')
        self.assertTrue(np.isfinite(E).all());self.assertTrue(np.all(np.diag(E)==0))
        self.assertTrue(np.all(decay_A(np.array([[0,120],[120,0]]),'exponential',250)>=0))
    def test_synthetic_boundary_file_and_lisa_map_when_available(self):
        try:
            import geopandas as gpd
        except ImportError:
            self.skipTest('geopandas is optional')
        import pandas as pd
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'fictional.geojson'
            frame=gpd.GeoDataFrame({'unit':['A','B','C'],'geometry':[
                box(0,0,1,1),box(1,0,2,1),box(2,1,3,2)]},crs='EPSG:4326')
            frame.to_file(path,driver='GeoJSON')
            self.assertEqual(contiguity_A_from_boundary_file(str(path),'unit','queen',['A','B','C']).sum(),4)
            self.assertEqual(contiguity_A_from_boundary_file(str(path),'unit','rook',['A','B','C']).sum(),2)
            lisa=pd.DataFrame({'unit':['A','B','C'],'cluster':['HH','NS','LL']})
            dest=Path(tmp)/'lisa.png'
            lisa_map_if_boundary(lisa,str(path),'unit',dest)
            self.assertTrue(dest.is_file() and dest.stat().st_size>0)
    def test_gaussian_kernel_and_zero_variance_guard(self):
        E,m=economic_A(np.array([0.,1.,2.]),'gaussian',bandwidth=1.)
        self.assertAlmostEqual(E[0,1],float(np.exp(-0.5)),places=10)
        W=row_standardize(np.ones((4,4))-np.eye(4))
        self.assertTrue(np.isnan(bivariate_moran_i(np.ones(4),np.arange(4.),W)))
    def test_moran_and_lisa(self):
        W=np.ones((4,4))-np.eye(4);W=row_standardize(W)
        x=np.array([1.,2.,3.,4.]);y=np.array([3.,4.,1.,2.])
        self.assertAlmostEqual(moran_i(x,W),-1/3,places=7)
        self.assertTrue(np.isfinite(bivariate_moran_i(x,y,W)))
        out=local_moran(x,W,99,2)
        self.assertEqual(len(out),4);self.assertTrue(out['p_perm'].between(0,1).all())
    def test_rho_bounds_not_clamped_to_minus_one(self):
        W=np.array([[0,.5,.5],[.5,0,.5],[.5,.5,0]])
        lo,hi=PanelEngine.admissible_rho_bounds(W)
        self.assertLess(lo,-1.0);self.assertLess(hi,1.01)

if __name__=='__main__': unittest.main()
