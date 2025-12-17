"""
User-friendly error message mapping system.

This module maps technical errors to user-friendly messages with actionable guidance,
while maintaining detailed technical information in logs.
"""
from typing import Optional, Dict, Any
import re


class ErrorMessageMapper:
    """
    Maps technical errors to user-friendly messages.
    
    Provides both user-friendly messages for display and detailed technical
    information for logging purposes.
    """
    
    # Error pattern mappings (regex patterns -> user-friendly messages)
    ERROR_PATTERNS = {
        # Database errors
        r'no such table': {
            'user_message': 'O banco de dados não está configurado corretamente. Por favor, reinicie o aplicativo.',
            'action': 'Reinicie o aplicativo para recriar o banco de dados.'
        },
        r'unique constraint|UNIQUE constraint': {
            'user_message': 'Esta multa já foi cadastrada no sistema.',
            'action': 'A multa já existe no banco de dados. Nenhuma ação necessária.'
        },
        r'not enough values|operational error': {
            'user_message': 'Erro ao salvar dados no banco de dados.',
            'action': 'Verifique se todos os campos obrigatórios estão preenchidos.'
        },
        r'cannot connect|connection.*failed': {
            'user_message': 'Não foi possível conectar ao banco de dados.',
            'action': 'Verifique se o arquivo do banco de dados não está sendo usado por outro programa.'
        },
        
        # PDF parsing errors
        r'cannot open|file.*not found|no such file': {
            'user_message': 'Arquivo PDF não encontrado ou não pode ser aberto.',
            'action': 'Verifique se o arquivo existe e não está corrompido.'
        },
        r'pdf.*invalid|corrupted|damaged': {
            'user_message': 'O arquivo PDF está corrompido ou em formato inválido.',
            'action': 'Tente abrir o PDF em outro programa para verificar se está íntegro.'
        },
        r'permission denied|access denied': {
            'user_message': 'Sem permissão para acessar o arquivo.',
            'action': 'Verifique as permissões do arquivo ou mova-o para outra localização.'
        },
        r'failed to parse|missing.*field|required.*field': {
            'user_message': 'Não foi possível extrair informações do PDF.',
            'action': 'O PDF pode estar em um formato diferente do esperado. Verifique se é um PDF de multa válido.'
        },
        
        # Calendar API errors
        r'authentication.*failed|invalid.*credentials|token.*expired': {
            'user_message': 'Erro de autenticação com o Google Calendar.',
            'action': 'Reautorize o acesso ao Google Calendar nas configurações.'
        },
        r'quota.*exceeded|rate.*limit': {
            'user_message': 'Limite de requisições ao Google Calendar excedido.',
            'action': 'Aguarde alguns minutos e tente novamente.'
        },
        r'calendar.*not found|permission.*denied': {
            'user_message': 'Não foi possível acessar o Google Calendar.',
            'action': 'Verifique se você tem permissão para criar eventos no calendário.'
        },
        r'network.*error|connection.*timeout|failed.*request': {
            'user_message': 'Erro de conexão com o Google Calendar.',
            'action': 'Verifique sua conexão com a internet e tente novamente.'
        },
        
        # File system errors
        r'folder.*not found|directory.*not found': {
            'user_message': 'Pasta não encontrada.',
            'action': 'Verifique se o caminho da pasta está correto.'
        },
        r'not a directory': {
            'user_message': 'O caminho especificado não é uma pasta.',
            'action': 'Selecione uma pasta válida contendo os arquivos PDF.'
        },
        
        # General errors
        r'value.*error|invalid.*value': {
            'user_message': 'Valor inválido encontrado nos dados.',
            'action': 'Verifique os dados do arquivo e tente novamente.'
        },
        r'type.*error|attribute.*error': {
            'user_message': 'Erro interno do aplicativo.',
            'action': 'Reinicie o aplicativo. Se o problema persistir, verifique o arquivo de log.'
        },
    }
    
    # Default messages
    DEFAULT_USER_MESSAGE = 'Ocorreu um erro inesperado.'
    DEFAULT_ACTION = 'Verifique o arquivo de log para mais detalhes ou reinicie o aplicativo.'
    
    @classmethod
    def get_user_friendly_message(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Get user-friendly error message and action guidance.
        
        Args:
            error: The exception that occurred
            context: Optional context dictionary with additional information
        
        Returns:
            Dictionary with 'message' (user-friendly message) and 'action' (actionable guidance)
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check patterns
        for pattern, message_info in cls.ERROR_PATTERNS.items():
            if re.search(pattern, error_str, re.IGNORECASE):
                return {
                    'message': message_info['user_message'],
                    'action': message_info.get('action', cls.DEFAULT_ACTION)
                }
        
        # Type-specific handling
        if error_type == 'FileNotFoundError':
            return {
                'message': 'Arquivo não encontrado.',
                'action': 'Verifique se o arquivo existe no local especificado.'
            }
        elif error_type == 'PermissionError':
            return {
                'message': 'Sem permissão para acessar o recurso.',
                'action': 'Verifique as permissões do arquivo ou pasta.'
            }
        elif error_type == 'ValueError':
            return {
                'message': 'Valor inválido encontrado.',
                'action': 'Verifique os dados e tente novamente.'
            }
        elif error_type == 'KeyError':
            return {
                'message': 'Informação necessária não encontrada.',
                'action': 'Verifique se o arquivo contém todas as informações necessárias.'
            }
        elif error_type == 'sqlite3.OperationalError':
            return {
                'message': 'Erro na operação do banco de dados.',
                'action': 'Verifique se o banco de dados não está corrompido.'
            }
        elif error_type == 'sqlite3.IntegrityError':
            return {
                'message': 'Violação de integridade do banco de dados.',
                'action': 'A multa pode já estar cadastrada ou há dados duplicados.'
            }
        
        # Default fallback
        return {
            'message': cls.DEFAULT_USER_MESSAGE,
            'action': cls.DEFAULT_ACTION
        }
    
    @classmethod
    def format_error_for_user(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format error message for user display.
        
        Combines user-friendly message with actionable guidance.
        
        Args:
            error: The exception that occurred
            context: Optional context dictionary
        
        Returns:
            Formatted string ready for display to user
        """
        error_info = cls.get_user_friendly_message(error, context)
        return f"{error_info['message']}\n\n{error_info['action']}"
    
    @classmethod
    def get_log_message(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get detailed technical message for logging.
        
        Args:
            error: The exception that occurred
            context: Optional context dictionary
        
        Returns:
            Detailed technical message for logging
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        log_parts = [f"{error_type}: {error_msg}"]
        
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            log_parts.append(f"Context: {context_str}")
        
        return " | ".join(log_parts)

