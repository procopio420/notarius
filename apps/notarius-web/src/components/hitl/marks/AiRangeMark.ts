/**
 * TipTap Mark extension for AI suggestion target ranges
 * Temporary visual indicator for suggestion ranges
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export interface AiRangeOptions {
  HTMLAttributes: Record<string, any>;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    aiRange: {
      /**
       * Set an AI range mark
       */
      setAiRange: (attributes: { suggestionId: string }) => ReturnType;
      /**
       * Toggle an AI range mark
       */
      toggleAiRange: (attributes: { suggestionId: string }) => ReturnType;
      /**
       * Unset an AI range mark
       */
      unsetAiRange: () => ReturnType;
    };
  }
}

export const AiRangeMark = Mark.create<AiRangeOptions>({
  name: 'aiRange',

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      suggestionId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-suggestion-id'),
        renderHTML: (attributes) => {
          if (!attributes.suggestionId) {
            return {};
          }
          return {
            'data-suggestion-id': attributes.suggestionId,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-suggestion-id]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'ai-range-mark bg-yellow-100 border border-yellow-300 px-0.5 rounded',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      setAiRange:
        (attributes) =>
        ({ commands }) => {
          return commands.setMark(this.name, attributes);
        },
      toggleAiRange:
        (attributes) =>
        ({ commands }) => {
          return commands.toggleMark(this.name, attributes);
        },
      unsetAiRange:
        () =>
        ({ commands }) => {
          return commands.unsetMark(this.name);
        },
    };
  },
});


