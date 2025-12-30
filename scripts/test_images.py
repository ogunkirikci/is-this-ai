"""Test script for image detection.

Place example1.jpg and example2.jpg in test_images/ directory,
then run: python scripts/test_images.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.detectors import get_default_detector
from app.media.image import normalize_image
import tempfile

def test_image(image_path: str) -> None:
    """Test a single image and print results."""
    if not os.path.exists(image_path):
        print(f"❌ Dosya bulunamadı: {image_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"📸 Test ediliyor: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    detector = get_default_detector()
    
    with tempfile.TemporaryDirectory(prefix="test_") as tmp:
        proc_dir = os.path.join(tmp, "processed")
        
        # Normalize image
        try:
            norm_path = normalize_image(image_path, proc_dir, max_side=1024)
            print(f"✓ Görsel normalize edildi: {norm_path}")
        except Exception as e:
            print(f"❌ Normalizasyon hatası: {e}")
            return
        
        # Detect
        try:
            result = detector.detect_image(norm_path)
            
            # Print results
            print(f"\n📊 Sonuçlar:")
            print(f"   AI Olasılığı: %{int(result.score * 100)}")
            print(f"   Güven: %{int(result.confidence * 100)}")
            print(f"\n   Sinyaller:")
            for i, reason in enumerate(result.reasons, 1):
                print(f"   {i}. {reason}")
            
            # Format reply (like the bot would)
            from app.tasks import format_reply
            reply_text = format_reply(result.score, result.confidence, result.reasons)
            print(f"\n💬 Bot Yanıtı:")
            print(f"   {reply_text}")
            
        except Exception as e:
            print(f"❌ Tespit hatası: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main test function."""
    # Find test images directory
    project_root = Path(__file__).parent.parent
    test_dir = project_root / "test_images"
    
    if not test_dir.exists():
        print(f"📁 Test klasörü oluşturuluyor: {test_dir}")
        test_dir.mkdir()
        print(f"\n⚠️  Lütfen example1.jpg ve example2.jpg dosyalarını şu klasöre ekleyin:")
        print(f"   {test_dir}")
        return
    
    # Test images
    example1 = test_dir / "example1.jpg"
    example2 = test_dir / "example2.jpg"
    
    # Also check for .png, .jpeg extensions
    if not example1.exists():
        for ext in [".png", ".jpeg", ".JPG", ".PNG", ".JPEG"]:
            alt = test_dir / f"example1{ext}"
            if alt.exists():
                example1 = alt
                break
    
    if not example2.exists():
        for ext in [".png", ".jpeg", ".JPG", ".PNG", ".JPEG"]:
            alt = test_dir / f"example2{ext}"
            if alt.exists():
                example2 = alt
                break
    
    print("🤖 isthisai-bot Test Script")
    print(f"📂 Test klasörü: {test_dir}\n")
    
    if example1.exists():
        test_image(str(example1))
    else:
        print(f"⚠️  example1.jpg bulunamadı")
    
    if example2.exists():
        test_image(str(example2))
    else:
        print(f"⚠️  example2.jpg bulunamadı")
    
    if not example1.exists() and not example2.exists():
        print(f"\n📝 Örnek dosyalar bulunamadı.")
        print(f"   Lütfen example1.jpg ve example2.jpg dosyalarını şu klasöre ekleyin:")
        print(f"   {test_dir}")

if __name__ == "__main__":
    main()

