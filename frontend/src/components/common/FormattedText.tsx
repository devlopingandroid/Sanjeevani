import React from 'react';
import { View, Text, StyleSheet, TextStyle, ViewStyle } from 'react-native';
import { colors, typography, spacing } from '../../theme';

interface FormattedTextProps {
  content: string;
  textColor?: string;
  style?: ViewStyle;
}

export const FormattedText: React.FC<FormattedTextProps> = ({
  content,
  textColor = colors.textPrimary,
  style,
}) => {
  if (!content) return null;

  // Render inline formatting (**bold**) safely without leaving stray ** asterisks
  const renderInlineText = (text: string, baseStyle: TextStyle) => {
    // Clean up empty/double bold tokens like ****
    const cleanStr = text.replace(/\*\*\s*\*\*/g, '');
    const parts = cleanStr.split(/(\*\*.*?\*\*)/g);

    return (
      <Text style={baseStyle}>
        {parts.map((part, idx) => {
          if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
            const boldText = part.slice(2, -2).trim();
            if (!boldText) return null;
            return (
              <Text key={idx} style={[baseStyle, styles.boldText]}>
                {boldText}
              </Text>
            );
          }
          // Strip any stray ** from non-matching text chunks
          const safeText = part.replace(/\*\*/g, '');
          return safeText;
        })}
      </Text>
    );
  };

  // Split into raw lines / blocks
  const lines = content.split('\n');

  const elements: React.ReactNode[] = [];
  let blockKey = 0;

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i].trim();
    if (!rawLine) {
      // Empty line -> section spacing
      elements.push(<View key={`space-${blockKey++}`} style={styles.lineSpacer} />);
      continue;
    }

    // 1. Headings (###, ##, #)
    if (rawLine.startsWith('#')) {
      const cleanHeading = rawLine.replace(/^#+\s*/, '').replace(/\*\*/g, '').trim();
      elements.push(
        <View key={`h-${blockKey++}`} style={styles.headingWrapper}>
          <Text style={[styles.headingText, { color: colors.primaryDark }]}>
            {cleanHeading}
          </Text>
        </View>
      );
      continue;
    }

    // 2. Bullet points (•, -, *)
    if (rawLine.startsWith('•') || rawLine.startsWith('-') || rawLine.startsWith('*')) {
      const cleanBullet = rawLine.replace(/^[•\-\*]+\s*/, '').trim();
      elements.push(
        <View key={`b-${blockKey++}`} style={styles.listRow}>
          <Text style={styles.bulletSymbol}>•</Text>
          <View style={styles.listTextContainer}>
            {renderInlineText(cleanBullet, { color: textColor, fontSize: typography.size.sm, lineHeight: 22 })}
          </View>
        </View>
      );
      continue;
    }

    // 3. Numbered items (1., 2., etc.)
    const numberMatch = rawLine.match(/^(\d+)[\.\)]\s*(.*)/);
    if (numberMatch) {
      const num = numberMatch[1];
      const text = numberMatch[2];
      elements.push(
        <View key={`num-${blockKey++}`} style={styles.listRow}>
          <Text style={styles.numberSymbol}>{num}.</Text>
          <View style={styles.listTextContainer}>
            {renderInlineText(text, { color: textColor, fontSize: typography.size.sm, lineHeight: 22 })}
          </View>
        </View>
      );
      continue;
    }

    // 4. Regular Paragraphs
    elements.push(
      <View key={`p-${blockKey++}`} style={styles.paragraphWrapper}>
        {renderInlineText(rawLine, { color: textColor, fontSize: typography.size.sm, lineHeight: 22 })}
      </View>
    );
  }

  return <View style={[styles.container, style]}>{elements}</View>;
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  lineSpacer: {
    height: 8,
  },
  headingWrapper: {
    marginTop: 10,
    marginBottom: 4,
  },
  headingText: {
    fontSize: typography.size.sm + 2,
    fontWeight: typography.weight.bold,
    lineHeight: 22,
  },
  boldText: {
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  listRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 4,
    marginBottom: 4,
    paddingRight: 4,
  },
  bulletSymbol: {
    fontSize: 16,
    color: colors.primary,
    fontWeight: 'bold',
    marginRight: 8,
    lineHeight: 22,
  },
  numberSymbol: {
    fontSize: typography.size.sm,
    color: colors.primaryDark,
    fontWeight: typography.weight.bold,
    marginRight: 8,
    minWidth: 18,
    lineHeight: 22,
  },
  listTextContainer: {
    flex: 1,
  },
  paragraphWrapper: {
    marginBottom: 8,
  },
});


