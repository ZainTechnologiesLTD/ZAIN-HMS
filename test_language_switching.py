#!/usr/bin/env python3
"""
Test script to verify language switching functionality in ZAIN HMS
"""
import requests
import sys

def test_language_switching():
    base_url = "http://127.0.0.1:8001"
    languages = ['en', 'es', 'fr', 'ar', 'hi', 'pt', 'de', 'it']

    print("Testing language switching functionality...")
    print("=" * 50)

    for lang in languages:
        try:
            # Test language switching
            response = requests.post(
                f"{base_url}/set_language/",
                data={
                    'language': lang,
                    'next': '/'
                },
                allow_redirects=True
            )

            if response.status_code == 200:
                print(f"✅ {lang}: Language switching successful")
                # Check if the response contains the correct language code
                if f'lang="{lang}"' in response.text:
                    print(f"   ✅ HTML lang attribute correctly set to '{lang}'")
                else:
                    print(f"   ⚠️  HTML lang attribute not found or incorrect")

                # Check for RTL support for Arabic
                if lang == 'ar':
                    if 'dir="rtl"' in response.text:
                        print(f"   ✅ RTL direction correctly set for Arabic")
                    else:
                        print(f"   ⚠️  RTL direction not found for Arabic")
            else:
                print(f"❌ {lang}: Language switching failed (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"❌ {lang}: Request failed - {e}")

        print()

    print("Language switching test completed!")

if __name__ == "__main__":
    test_language_switching()
