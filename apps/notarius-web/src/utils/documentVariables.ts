/**
 * Utilities for manipulating document variables and placeholders
 */

export interface DocumentVariable {
  name: string;
  placeholder: string;
  value: string;
  isPII: boolean;
}

/**
 * Extract all variables from document content
 */
export function extractVariablesFromDocument(content: string): DocumentVariable[] {
  const placeholderRegex = /\{\{([^}]+)\}\}/g;
  const variables: DocumentVariable[] = [];
  const seen = new Set<string>();
  
  let match;
  while ((match = placeholderRegex.exec(content)) !== null) {
    const placeholder = match[0]; // {{VARIABLE_NAME}}
    const variableName = match[1]; // VARIABLE_NAME
    
    if (!seen.has(variableName)) {
      seen.add(variableName);
      variables.push({
        name: variableName,
        placeholder,
        value: '', // Will be filled from variaveis_json
        isPII: isPIIVariable(variableName)
      });
    }
  }
  
  return variables;
}

/**
 * Check if a variable name looks like PII
 */
function isPIIVariable(variableName: string): boolean {
  const piiPatterns = [
    /cpf/i,
    /cnpj/i,
    /rg/i,
    /nome/i,
    /endereco/i,
    /telefone/i,
    /email/i,
    /data/i,
    /nascimento/i,
    /outorgante/i,
    /outorgado/i,
    /parte/i
  ];
  
  return piiPatterns.some(pattern => pattern.test(variableName));
}

/**
 * Replace a variable in document content
 */
export function replaceVariableInDocument(
  content: string, 
  variableName: string, 
  newValue: string
): string {
  const placeholder = `{{${variableName}}}`;
  const regex = new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
  return content.replace(regex, newValue);
}

/**
 * Toggle variable display between placeholders and real values
 */
export function toggleVariableDisplay(
  content: string,
  variables: DocumentVariable[],
  showRealValues: boolean
): string {
  let result = content;
  
  variables.forEach(variable => {
    if (showRealValues) {
      // Replace placeholder with real value
      result = replaceVariableInDocument(result, variable.name, variable.value);
    } else {
      // Replace real value with placeholder
      if (variable.value) {
        const valueRegex = new RegExp(variable.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
        result = result.replace(valueRegex, variable.placeholder);
      }
    }
  });
  
  return result;
}

/**
 * Update variable values from variaveis_json
 */
export function updateVariableValues(
  variables: DocumentVariable[],
  variaveisJson: Record<string, unknown>
): DocumentVariable[] {
  return variables.map(variable => ({
    ...variable,
    value: variaveisJson[variable.name] || ''
  }));
}

/**
 * Get variables that have been modified
 */
export function getModifiedVariables(
  originalVariables: DocumentVariable[],
  currentVariables: DocumentVariable[]
): DocumentVariable[] {
  return currentVariables.filter(current => {
    const original = originalVariables.find(v => v.name === current.name);
    return original && original.value !== current.value;
  });
}

/**
 * Validate variable values
 */
export function validateVariableValue(variableName: string, value: string): string | null {
  if (!value.trim()) {
    return null; // Empty values are allowed
  }
  
  // CPF validation
  if (/cpf/i.test(variableName)) {
    const cpfRegex = /^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$/;
    if (!cpfRegex.test(value)) {
      return 'CPF deve ter o formato 000.000.000-00';
    }
  }
  
  // CNPJ validation
  if (/cnpj/i.test(variableName)) {
    const cnpjRegex = /^\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}$/;
    if (!cnpjRegex.test(value)) {
      return 'CNPJ deve ter o formato 00.000.000/0000-00';
    }
  }
  
  // Email validation
  if (/email/i.test(variableName)) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Email deve ter um formato válido';
    }
  }
  
  return null;
}

/**
 * Format variable value for display
 */
export function formatVariableValue(variableName: string, value: string): string {
  if (!value) return '';
  
  // Format CPF
  if (/cpf/i.test(variableName)) {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length === 11) {
      return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
  }
  
  // Format CNPJ
  if (/cnpj/i.test(variableName)) {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length === 14) {
      return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
  }
  
  return value;
}

/**
 * Parse variable value for storage
 */
export function parseVariableValue(variableName: string, value: string): string {
  if (!value) return '';
  
  // Remove formatting for CPF/CNPJ
  if (/cpf/i.test(variableName) || /cnpj/i.test(variableName)) {
    return value.replace(/\D/g, '');
  }
  
  return value.trim();
}

