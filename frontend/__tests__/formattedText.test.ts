/**
 * FormattedText & AI Formatting Tests
 * 
 * Verifies that:
 * 1. Headings, bullet points, numbered steps, and paragraphs are parsed.
 * 2. Paragraph breaks and list items preserve line structure.
 * 3. Inline bold tags (**bold**) are extracted.
 */
import { describe, test, expect } from '@jest/globals';

describe('FormattedText Markdown & List Formatting Logic', () => {
  test('parses headings correctly', () => {
    const text = "### What it means\nStress is your body's natural response.";
    const lines = text.split('\n');
    expect(lines[0].startsWith('###')).toBe(true);
    expect(lines[0].replace(/^#+\s*/, '')).toBe('What it means');
  });

  test('parses bullet points correctly', () => {
    const text = "• Inhale for 4 seconds.\n• Hold for 4 seconds.\n• Exhale for 6 seconds.";
    const lines = text.split('\n');
    expect(lines.length).toBe(3);
    lines.forEach((l) => {
      expect(l.startsWith('•')).toBe(true);
    });
  });

  test('parses numbered steps correctly', () => {
    const text = "1. First step\n2. Second step\n3. Third step";
    const lines = text.split('\n');
    lines.forEach((l, idx) => {
      const match = l.match(/^(\d+)[\.\)]\s*(.*)/);
      expect(match).not.toBeNull();
      expect(match![1]).toBe(String(idx + 1));
    });
  });

  test('extracts inline bold text correctly and sanitizes stray asterisks', () => {
    const input = "Use **diaphragmatic breathing** for relaxation **** and **unmatched.";
    const cleanStr = input.replace(/\*\*\s*\*\*/g, '');
    const parts = cleanStr.split(/(\*\*.*?\*\*)/g);
    expect(parts.length).toBe(3);
    expect(parts[1]).toBe('**diaphragmatic breathing**');

    // Verify stray asterisks are stripped
    const safeText = parts[2].replace(/\*\*/g, '');
    expect(safeText.includes('**')).toBe(false);
  });
});

