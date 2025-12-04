#!/usr/bin/env python3
"""
Test script for Bershka scraper fixes
Tests the API functionality without requiring database connection
"""
import asyncio
import os
import sys
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bershka_scraper import load_product_ids_from_url_async, BershkaScraper
from config import CATEGORY_IDS


async def test_product_id_loading():
    """Test that product ID loading works correctly."""
    print("Testing product ID loading functionality...")

    # Test with just one category to avoid rate limiting
    test_category_id = '1010193212'  # Women's jackets_coats

    # Mock category URLs (simplified version)
    mock_urls = {
        '1010193212': 'https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/category/1010193212/product?showProducts=false&showNoStock=false&appId=1&languageId=-15&locale=en_GB'
    }

    print(f"Testing category ID: {test_category_id}")

    try:
        # Test loading product IDs from URL
        print("1. Testing product ID loading from URL...")
        product_ids = await load_product_ids_from_url_async(test_category_id, mock_urls)

        if product_ids:
            print(f"   ✓ Successfully loaded {len(product_ids)} product IDs")
            print(f"   Sample IDs: {product_ids[:5]}")
            return len(product_ids) > 0
        else:
            print("   ✗ Failed to load product IDs from URL")
            return False

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False


async def test_api_url_building():
    """Test that API URL building works correctly."""
    print("Testing API URL building...")

    try:
        # Create a minimal scraper instance just to test URL building
        scraper = BershkaScraper.__new__(BershkaScraper)  # Create without __init__

        # Test basic URL building
        url = scraper.build_api_url(1010193212, None, None)
        expected_base = "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193212&appId=1&languageId=-15&locale=en_GB"
        if url == expected_base:
            print("   ✓ Basic URL building works")
        else:
            print(f"   ✗ URL mismatch. Expected: {expected_base}, Got: {url}")
            return False

        # Test URL with product IDs
        test_ids = [123, 456, 789]
        url_with_ids = scraper.build_api_url(1010193212, test_ids, None)
        if "&productIds=123%2C456%2C789" in url_with_ids:
            print("   ✓ URL building with product IDs works")
        else:
            print(f"   ✗ Product IDs not properly encoded in URL: {url_with_ids}")
            return False

        return True

    except Exception as e:
        print(f"✗ URL building test failed: {e}")
        return False


async def test_title_extraction_fix():
    """Test that products without titles get default titles."""
    print("Testing title extraction fix...")

    try:
        # Create a minimal scraper instance
        scraper = BershkaScraper.__new__(BershkaScraper)  # Create without __init__

        # Test data: product with no nameEn or name field but with image
        bundle_product_no_title = {
            'id': 12345,
            # No nameEn or name fields
            'bundleProductSummaries': [{
                'detail': {
                    'xmedia': [{
                        'xmediaItems': [{
                            'medias': [{
                                'url': 'https://static.bershka.net/assets/public/test/image.jpg',
                                'extraInfo': {
                                    'originalName': 's1',
                                    'deliveryUrl': 'https://static.bershka.net/assets/public/test/image.jpg'
                                }
                            }]
                        }]
                    }],
                    'colors': [{
                        'id': 2025,
                        'reference': 'TEST123',
                        'sizes': [{'name': 'M', 'price': '2990', 'isBuyable': True}]
                    }]
                },
                'sectionNameEN': 'WOMAN',
                'productUrl': 'test-product'
            }]
        }

        variant = bundle_product_no_title['bundleProductSummaries'][0]
        color = variant['detail']['colors'][0]

        # Test the extraction
        result = scraper._extract_single_product(bundle_product_no_title, variant, color)

        if result and result['title'] == 'Unknown Product':
            print("   ✓ Products without titles get default title 'Unknown Product'")
            return True
        else:
            print(f"   ✗ Title extraction failed. Got: {result.get('title') if result else 'None'}")
            return False

    except Exception as e:
        print(f"✗ Title extraction test failed: {e}")
        return False


async def test_deterministic_id_generation():
    """Test that ID generation is deterministic and unique."""
    print("Testing deterministic ID generation...")

    try:
        from bershka_scraper import generate_deterministic_id

        # Test that same source + product_url always generates same ID
        source = "scraper"
        product_url1 = "https://www.bershka.com/us/test-product.html"
        product_url2 = "https://www.bershka.com/us/different-product.html"

        id1a = generate_deterministic_id(source, product_url1)
        id1b = generate_deterministic_id(source, product_url1)
        id2 = generate_deterministic_id(source, product_url2)

        if id1a == id1b:
            print("   ✓ Same source+URL generates consistent ID")
        else:
            print(f"   ✗ Inconsistent ID generation: {id1a} != {id1b}")
            return False

        if id1a != id2:
            print("   ✓ Different URLs generate different IDs")
        else:
            print("   ✗ Different URLs generated same ID (collision)")
            return False

        # Test ID length (SHA256 hex is 64 characters)
        if len(id1a) == 64 and id1a.isalnum():
            print("   ✓ ID has correct format (64-char hex)")
        else:
            print(f"   ✗ ID format incorrect: {id1a}")
            return False

        return True

    except Exception as e:
        print(f"✗ ID generation test failed: {e}")
        return False


async def main():
    """Run the API functionality tests."""
    print("=" * 60)
    print("BERSHKA SCRAPER API FIXES TEST")
    print("=" * 60)

    print("Note: This test focuses on the fixes without requiring Supabase credentials")
    print()

    # Test 1: API URL building
    url_test_passed = await test_api_url_building()
    print()

    # Test 2: Product ID loading (requires internet)
    id_test_passed = await test_product_id_loading()
    print()

    # Test 3: Title extraction fix
    title_test_passed = await test_title_extraction_fix()
    print()

    # Test 4: Deterministic ID generation
    id_gen_test_passed = await test_deterministic_id_generation()
    print()

    success = url_test_passed and id_test_passed and title_test_passed and id_gen_test_passed

    print("=" * 60)
    if success:
        print("✓ ALL TESTS PASSED - API fixes are working!")
        print("The scraper should now work correctly without null title errors.")
    else:
        print("✗ SOME TESTS FAILED - Check the fixes")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
