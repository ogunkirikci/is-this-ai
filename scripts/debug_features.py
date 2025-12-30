"""Debug script to see feature values for test images."""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.detectors.heuristic import HeuristicDetector
from app.media.image import normalize_image
import tempfile

def debug_image(image_path: str) -> None:
    """Debug a single image and print all features."""
    if not os.path.exists(image_path):
        print(f"❌ Dosya bulunamadı: {image_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 Debug: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    detector = HeuristicDetector()
    
    with tempfile.TemporaryDirectory(prefix="debug_") as tmp:
        proc_dir = os.path.join(tmp, "processed")
        norm_path = normalize_image(image_path, proc_dir, max_side=1024)
        
        from PIL import Image
        img = Image.open(norm_path)
        feats = detector._image_features(img)
        
        print(f"\n📊 Feature Değerleri:")
        print(f"   hf_energy (yüksek-frekans enerjisi): {feats['hf_energy']:.6f}")
        print(f"   sat_mean (ortalama doygunluk): {feats['sat_mean']:.6f}")
        print(f"   sat_p95 (doygunluk %95): {feats['sat_p95']:.6f}")
        print(f"   edge_density (kenar yoğunluğu): {feats['edge_density']:.6f}")
        if 'texture_uniformity' in feats:
            print(f"   texture_uniformity (doku tekdüzeliği): {feats['texture_uniformity']:.6f}")
        if 'has_watermark' in feats:
            print(f"   has_watermark (watermark var mı): {feats['has_watermark']}")
            if feats['has_watermark']:
                print(f"   watermark_reason: {feats.get('watermark_reason', '')}")
        
        print(f"\n🎯 Threshold Kontrolleri:")
        print(f"   hf_energy < 0.02? {feats['hf_energy'] < 0.02} (değer: {feats['hf_energy']:.6f})")
        print(f"   hf_energy < 0.025? {feats['hf_energy'] < 0.025} (değer: {feats['hf_energy']:.6f})")
        if 'texture_uniformity' in feats:
            print(f"   texture_uniformity > 0.4? {feats['texture_uniformity'] > 0.4} (değer: {feats['texture_uniformity']:.6f})")
            print(f"   texture_uniformity > 0.5? {feats['texture_uniformity'] > 0.5} (değer: {feats['texture_uniformity']:.6f})")
        print(f"   edge_density < 0.06? {feats['edge_density'] < 0.06} (değer: {feats['edge_density']:.6f})")
        print(f"   edge_density < 0.08? {feats['edge_density'] < 0.08} (değer: {feats['edge_density']:.6f})")
        print(f"   sat_mean > 0.40? {feats['sat_mean'] > 0.40} (değer: {feats['sat_mean']:.6f})")
        
        result = detector.detect_image(norm_path)
        print(f"\n📈 Sonuç:")
        print(f"   Score: {result.score:.2f} ({int(result.score * 100)}%)")
        print(f"   Confidence: {result.confidence:.2f} ({int(result.confidence * 100)}%)")
        print(f"   Reasons: {result.reasons}")

def main():
    project_root = Path(__file__).parent.parent
    test_dir = project_root / "test_images"
    
    example1 = test_dir / "example1.jpeg"
    example2 = test_dir / "example2.JPG"
    
    if not example1.exists():
        for ext in [".jpg", ".png", ".JPG", ".PNG", ".JPEG"]:
            alt = test_dir / f"example1{ext}"
            if alt.exists():
                example1 = alt
                break
    
    if not example2.exists():
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".PNG", ".JPEG"]:
            alt = test_dir / f"example2{ext}"
            if alt.exists():
                example2 = alt
                break
    
    print("🔬 Feature Debug Script\n")
    
    if example1.exists():
        debug_image(str(example1))
    else:
        print(f"⚠️  example1 bulunamadı")
    
    if example2.exists():
        debug_image(str(example2))
    else:
        print(f"⚠️  example2 bulunamadı")

if __name__ == "__main__":
    main()

