/**
 * TipTap Mark extension for grounding (citation links)
 * Renders underline/marker with citation IDs
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export interface GroundingOptions {
  HTMLAttributes: Record<string, any>;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    grounding: {
      /**
       * Set a grounding mark
       */
      setGrounding: (attributes: { citationId: string }) => ReturnType;
      /**
       * Toggle a grounding mark
       */
      toggleGrounding: (attributes: { citationId: string }) => ReturnType;
      /**
       * Unset a grounding mark
       */
      unsetGrounding: () => ReturnType;
    };
  }
}

export const GroundingMark = Mark.create<GroundingOptions>({
  name: 'grounding',

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      citationId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-citation-id'),
        renderHTML: (attributes) => {
          if (!attributes.citationId) {
            return {};
          }
          return {
            'data-citation-id': attributes.citationId,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-citation-id]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'grounding-mark border-b-2 border-green-400 px-0.5',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      setGrounding:
        (attributes) =>
        ({ commands }) => {
          return commands.setMark(this.name, attributes);
        },
      toggleGrounding:
        (attributes) =>
        ({ commands }) => {
          return commands.toggleMark(this.name, attributes);
        },
      unsetGrounding:
        () =>
        ({ commands }) => {
          return commands.unsetMark(this.name);
        },
    };
  },
});


