/**
 * Right sidebar with tabs: Sugestões, Fundamentação, Checklist
 */

import React, { useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { ptBR } from '../../lib/i18n/ptBR';
import { Editor } from '@tiptap/react';
import { SuggestionsPanel } from './SuggestionsPanel';
import { GroundingPanel } from './GroundingPanel';
import { ChecklistPanel } from './ChecklistPanel';

interface HITLRightSidebarProps {
  editor: Editor | null;
}

export const HITLRightSidebar: React.FC<HITLRightSidebarProps> = ({ editor }) => {
  const [activeTab, setActiveTab] = useState('suggestions');

  return (
    <div className="w-[360px] border-l border-gray-200 bg-gray-50 flex flex-col overflow-hidden">
      <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
        <Tabs.List className="flex border-b border-gray-200 bg-white">
          <Tabs.Trigger
            value="suggestions"
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 transition-colors"
          >
            {ptBR.tabs.suggestions}
          </Tabs.Trigger>
          <Tabs.Trigger
            value="grounding"
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 transition-colors"
          >
            {ptBR.tabs.grounding}
          </Tabs.Trigger>
          <Tabs.Trigger
            value="checklist"
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 transition-colors"
          >
            {ptBR.tabs.checklist}
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="suggestions" className="flex-1 overflow-hidden">
          <SuggestionsPanel editor={editor} />
        </Tabs.Content>

        <Tabs.Content value="grounding" className="flex-1 overflow-hidden">
          <GroundingPanel editor={editor} />
        </Tabs.Content>

        <Tabs.Content value="checklist" className="flex-1 overflow-hidden">
          <ChecklistPanel />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
};


