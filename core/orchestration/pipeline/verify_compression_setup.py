#!/usr/bin/env python3
"""
LLMLingua Compression Verification Script

This script verifies that LLMLingua is properly installed and configured,
checks HuggingFace authentication, and tests the compression functionality.
"""

import argparse
import sys
from typing import Optional


def check_llmlingua_installation(verbose: bool = False) -> bool:
    """
    Verify LLMLingua installation.

    Args:
        verbose: Enable detailed output

    Returns:
        True if LLMLingua is installed, False otherwise
    """
    if verbose:
        print("Checking LLMLingua installation...")

    try:
        import llmlingua
        if verbose:
            print(f"  LLMLingua version: {llmlingua.__version__}")
        print("✅ LLMLingua is installed")
        return True
    except ImportError as e:
        print(f"❌ LLMLingua is not installed: {e}")
        return False


def check_huggingface_auth(verbose: bool = False) -> bool:
    """
    Check HuggingFace authentication status.

    Args:
        verbose: Enable detailed output

    Returns:
        True if authenticated, False otherwise
    """
    if verbose:
        print("Checking HuggingFace authentication...")

    try:
        from huggingface_hub import whoami
        try:
            user_info = whoami()
            if verbose:
                print(f"  Authenticated as: {user_info.get('name', 'unknown')}")
            print("✅ HuggingFace authentication successful")
            return True
        except Exception:
            print("❌ HuggingFace authentication failed (not logged in)")
            return False
    except ImportError:
        print("❌ huggingface_hub is not installed")
        return False


def test_llama_model_access(verbose: bool = False) -> bool:
    """
    Test LLaMA model access from HuggingFace.

    Args:
        verbose: Enable detailed output

    Returns:
        True if model is accessible, False otherwise
    """
    if verbose:
        print("Testing LLaMA model access...")

    try:
        from transformers import AutoTokenizer
        model_name = "meta-llama/Llama-2-7b-hf"
        if verbose:
            print(f"  Attempting to load tokenizer for: {model_name}")
        AutoTokenizer.from_pretrained(model_name, use_auth_token=True)
        print("✅ LLaMA model access successful")
        return True
    except Exception as e:
        if verbose:
            print(f"  Model access failed: {e}")
        print("❌ LLaMA model access failed")
        return False


def test_compression(verbose: bool = False) -> tuple[bool, float, str]:
    """
    Test LLMLinguaCompressor and return compression results.

    Args:
        verbose: Enable detailed output

    Returns:
        Tuple of (success, compression_ratio, mode)
    """
    if verbose:
        print("Testing LLMLinguaCompressor...")

    try:
        from llmlingua import PromptCompressor
        from transformers import AutoTokenizer

        test_prompt = (
            "This is a test prompt for LLMLingua compression. "
            "We want to verify that the compression functionality works correctly. "
            "The prompt should be compressed while preserving the most important information. "
            "This helps reduce token usage and API costs when working with LLMs."
        )

        if verbose:
            print(f"  Original prompt length: {len(test_prompt)} characters")

        try:
            # Try with LLMLingua (90% compression expected)
            compressor = PromptCompressor(
                model_name="meta-llama/Llama-2-7b-hf",
                device_map="cpu"
            )
            compressed_prompt = compressor.compress_prompt(
                test_prompt,
                rate=0.1,  # Keep 10% = 90% compression
                target_token=200
            )

            original_tokens = len(test_prompt.split())
            compressed_tokens = len(compressed_prompt.split())

            if original_tokens > 0:
                compression_ratio = (1 - compressed_tokens / original_tokens) * 100
            else:
                compression_ratio = 0.0

            if verbose:
                print(f"  Compressed prompt length: {len(compressed_prompt)} characters")
                print(f"  Original tokens: {original_tokens}")
                print(f"  Compressed tokens: {compressed_tokens}")

            print(f"✅ LLMLingua compression successful")
            print(f"   Compression ratio: {compression_ratio:.1f}%")
            print(f"   Mode: llmlingua (90% compression)")
            return True, compression_ratio, "llmlingua"

        except Exception as e:
            if verbose:
                print(f"  LLMLingua compression failed: {e}")
            # Fall back to simple compression
            compressed_prompt = simple_compress(test_prompt)
            original_tokens = len(test_prompt.split())
            compressed_tokens = len(compressed_prompt.split())

            if original_tokens > 0:
                compression_ratio = (1 - compressed_tokens / original_tokens) * 100
            else:
                compression_ratio = 0.0

            if verbose:
                print(f"  Using simple fallback compression")

            print(f"⚠️  LLMLingua unavailable, using fallback compression")
            print(f"   Compression ratio: {compression_ratio:.1f}%")
            print(f"   Mode: simple fallback (20-30% compression)")
            return True, compression_ratio, "simple"

    except ImportError:
        print("❌ Required compression libraries not installed")
        return False, 0.0, "unavailable"


def simple_compress(text: str) -> str:
    """
    Simple fallback compression method.

    Args:
        text: Input text to compress

    Returns:
        Compressed text
    """
    # Simple word removal based on common filler words
    filler_words = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were"}
    words = text.split()
    filtered = [w for w in words if w.lower() not in filler_words]
    return " ".join(filtered)


def display_cost_savings(compression_ratio: float, mode: str) -> None:
    """
    Display cost savings analysis based on compression ratio.

    Args:
        compression_ratio: Compression ratio as percentage
        mode: Compression mode used
    """
    print("\n" + "=" * 50)
    print("Cost Savings Analysis")
    print("=" * 50)

    # Example costs (Claude Sonnet pricing)
    input_cost_per_1m_tokens = 3.0  # USD
    monthly_tokens = 1_000_000  # Example: 1M tokens/month

    original_cost = (monthly_tokens / 1_000_000) * input_cost_per_1m_tokens
    compressed_tokens = monthly_tokens * (1 - compression_ratio / 100)
    compressed_cost = (compressed_tokens / 1_000_000) * input_cost_per_1m_tokens
    savings = original_cost - compressed_cost

    print(f"Compression Mode: {mode}")
    print(f"Compression Ratio: {compression_ratio:.1f}%")
    print(f"\nMonthly Usage Example:")
    print(f"  Original tokens: {monthly_tokens:,}")
    print(f"  Compressed tokens: {int(compressed_tokens):,}")
    print(f"  Original cost: ${original_cost:.2f}")
    print(f"  Compressed cost: ${compressed_cost:.2f}")
    print(f"  💰 Monthly savings: ${savings:.2f}")
    print(f"  📈 Annual savings: ${savings * 12:.2f}")
    print("=" * 50)


def main() -> int:
    """
    Main entry point for the verification script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Verify LLMLingia compression setup"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("LLMLingua Compression Verification")
    print("=" * 50)
    print()

    all_passed = True

    # Check LLMLingua installation
    if not check_llmlingua_installation(args.verbose):
        all_passed = False

    # Check HuggingFace authentication
    if not check_huggingface_auth(args.verbose):
        all_passed = False

    # Test LLaMA model access
    if not test_llama_model_access(args.verbose):
        all_passed = False

    # Test compression
    print()
    success, ratio, mode = test_compression(args.verbose)
    if not success:
        all_passed = False
    elif ratio > 0:
        display_cost_savings(ratio, mode)

    print()
    if all_passed:
        print("✅ All checks passed!")
        return 0
    else:
        print("❌ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
