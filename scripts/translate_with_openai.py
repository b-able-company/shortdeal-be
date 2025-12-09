#!/usr/bin/env python
"""
AI-powered translation script for ShortDeal platform
Uses OpenAI GPT-4 to translate UI strings with business-appropriate tone
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import openai
except ImportError:
    print("Error: openai package not installed")
    print("Please run: pip install openai")
    sys.exit(1)

try:
    import polib
except ImportError:
    print("Error: polib package not installed")
    print("Please run: pip install polib")
    sys.exit(1)


# OpenAI API key from environment
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("Error: OPENAI_API_KEY environment variable not set")
    print("Please set it with: export OPENAI_API_KEY='sk-...'")
    sys.exit(1)


TRANSLATION_SYSTEM_PROMPT = """You are a professional translator specializing in B2B platform localization for the short-form content trading industry.

Your task is to translate English UI text to Simplified Chinese (简体中文) for a professional content marketplace platform."""

TRANSLATION_USER_PROMPT_TEMPLATE = """Translate this English UI text to Simplified Chinese for a B2B short-form content trading platform.

**Context:**
- Industry: Short-form video/content licensing and trading
- Audience: Professional content creators (producers) and content buyers (B2B)
- Tone: Formal business communication
- Target: Simplified Chinese (简体中文) for mainland China market

**Terminology Guidelines (IMPORTANT):**
- "Short-form Content" → "短视频内容" (short video content, industry standard)
- "Producer" / "Content Creator" → "内容创作者" (content creator, professional)
- "Buyer" / "Content Buyer" → "内容采购方" (content purchaser, B2B tone)
- "Booth" → "创作者展位" (creator booth/showroom)
- "Content Trading" → "内容交易" (content trading/licensing)
- "Studio" → "创作工作室" (creator studio)
- "Browse" → "浏览"
- "Upload" → "上传"
- "Dashboard" → "工作台" (for creators) or "控制面板" (for admin)
- "Sign In" / "Login" → "登录"
- "Sign Up" / "Register" → "立即注册" (action-oriented, use polite imperative)
- "Submit" → "提交"
- "Hot Content" → "热门内容"
- "Featured" → "精选"
- "Trending" → "热门趋势"

**Style Requirements:**
- Use formal business Chinese (formal, professional tone)
- Avoid casual language or internet slang
- Be clear and direct for call-to-actions (CTAs)
- Use polite imperatives for action buttons (e.g., "立即注册" instead of just "注册")
- Maintain professional, trustworthy tone throughout

**English text to translate:**
"{text}"

**Instructions:**
- Return ONLY the Simplified Chinese translation
- Do NOT include any explanations, notes, or the original English text
- Do NOT add quotation marks around the translation
- Preserve any HTML tags if present (e.g., <strong>, <span>)
- If the text contains format placeholders like {{{{ variable }}}}, keep them unchanged"""


def translate_text(english_text: str) -> str:
    """
    Translate English text to Simplified Chinese using OpenAI GPT-4

    Args:
        english_text: The English text to translate

    Returns:
        The Chinese translation
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai.api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": TRANSLATION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": TRANSLATION_USER_PROMPT_TEMPLATE.format(text=english_text)
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent translations
            max_tokens=500
        )

        translation = response.choices[0].message.content.strip()
        # Remove quotes if AI added them
        if translation.startswith('"') and translation.endswith('"'):
            translation = translation[1:-1]
        if translation.startswith("'") and translation.endswith("'"):
            translation = translation[1:-1]

        return translation

    except Exception as e:
        print(f"Error translating '{english_text}': {e}")
        return english_text  # Return original on error


def process_po_file(po_file_path: Path, dry_run: bool = False):
    """
    Process a .po file and translate all untranslated strings

    Args:
        po_file_path: Path to the .po file
        dry_run: If True, don't save changes (for testing)
    """
    if not po_file_path.exists():
        print(f"Error: File not found: {po_file_path}")
        return

    print(f"\nProcessing: {po_file_path}")
    print("=" * 60)

    po = polib.pofile(str(po_file_path))

    # Count entries
    total_entries = len(po)
    untranslated = len([e for e in po if not e.msgstr and not e.obsolete])

    print(f"Total entries: {total_entries}")
    print(f"Untranslated: {untranslated}")
    print()

    if untranslated == 0:
        print("✓ All strings are already translated!")
        return

    # Translate each entry
    translated_count = 0
    for entry in po:
        # Skip if already translated or is obsolete
        if entry.msgstr or entry.obsolete:
            continue

        # Skip empty strings
        if not entry.msgid:
            continue

        print(f"[{translated_count + 1}/{untranslated}] Translating: {entry.msgid[:60]}...")

        translation = translate_text(entry.msgid)
        entry.msgstr = translation

        print(f"  → {translation}")
        print()

        translated_count += 1

    # Save the file
    if not dry_run:
        po.save(str(po_file_path))
        print(f"\n✓ Saved {translated_count} translations to {po_file_path}")
    else:
        print(f"\n[DRY RUN] Would save {translated_count} translations")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Translate Django .po files using OpenAI GPT-4"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save changes, just show what would be translated"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Specific .po file to translate (default: locale/zh_Hans/LC_MESSAGES/django.po)"
    )

    args = parser.parse_args()

    if args.file:
        po_file = Path(args.file)
    else:
        # Default to Chinese translation file
        po_file = project_root / 'locale' / 'zh_Hans' / 'LC_MESSAGES' / 'django.po'

    if not po_file.exists():
        print(f"Error: File not found: {po_file}")
        print("\nPlease run 'python manage.py makemessages -l zh_Hans' first")
        sys.exit(1)

    print("ShortDeal AI Translation Tool")
    print("=" * 60)
    print(f"Using OpenAI API key: {openai.api_key[:10]}...")
    print()

    if args.dry_run:
        print("*** DRY RUN MODE - No changes will be saved ***\n")

    process_po_file(po_file, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("Translation complete!")
    print("\nNext steps:")
    print("1. Review the translations in the .po file")
    print("2. Run: python manage.py compilemessages")
    print("3. Restart your Django server")
    print("4. Test the language switcher in your browser")


if __name__ == '__main__':
    main()
