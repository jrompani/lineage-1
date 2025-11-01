"""
Comando Django para backup de arquivos de mídia

Uso:
    python manage.py backup_media --create    # Cria backup
    python manage.py backup_media --restore   # Restaura backup
    python manage.py backup_media --list      # Lista backups disponíveis
"""

import os
import shutil
import zipfile
import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from django.conf import settings


class Command(BaseCommand):
    help = 'Utilitário para backup de arquivos de mídia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create',
            action='store_true',
            help='Cria um backup dos arquivos de mídia',
        )
        parser.add_argument(
            '--restore',
            type=str,
            help='Restaura backup do arquivo especificado',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista backups disponíveis',
        )
        parser.add_argument(
            '--path',
            type=str,
            help='Caminho específico para backup (opcional)',
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups/media',
            help='Diretório para salvar backups (padrão: backups/media)',
        )

    def handle(self, *args, **options):
        if options['create']:
            self.create_backup(options['path'], options['backup_dir'])
        elif options['restore']:
            self.restore_backup(options['restore'], options['backup_dir'])
        elif options['list']:
            self.list_backups(options['backup_dir'])
        else:
            self.stdout.write(
                self.style.ERROR('Especifique uma ação: --create, --restore ou --list')
            )

    def create_backup(self, specific_path, backup_dir):
        """Cria backup dos arquivos de mídia"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'media_backup_{timestamp}.zip'
        backup_path = os.path.join(backup_dir, backup_filename)

        # Criar diretório de backup se não existir
        os.makedirs(backup_dir, exist_ok=True)

        self.stdout.write(
            self.style.SUCCESS(f'📦 Criando backup: {backup_filename}\n')
        )

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Determinar caminho para backup
                if specific_path:
                    source_path = specific_path
                else:
                    source_path = getattr(settings, 'MEDIA_ROOT', 'media')

                if os.path.exists(source_path):
                    # Backup de storage local
                    self.add_local_files_to_zip(zipf, source_path)
                else:
                    # Backup de storage remoto
                    self.add_remote_files_to_zip(zipf)

            # Verificar tamanho do backup
            backup_size = os.path.getsize(backup_path)
            size_mb = backup_size / (1024 * 1024)

            self.stdout.write(
                self.style.SUCCESS(f'✅ Backup criado com sucesso!')
            )
            self.stdout.write(f'📁 Arquivo: {backup_path}')
            self.stdout.write(f'📊 Tamanho: {size_mb:.2f} MB')

        except Exception as e:
            raise CommandError(f'Erro ao criar backup: {e}')

    def add_local_files_to_zip(self, zipf, source_path):
        """Adiciona arquivos locais ao ZIP"""
        file_count = 0
        for root, dirs, files in os.walk(source_path):
            # Pular diretórios de backup e cache
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'backups']
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, source_path)
                
                try:
                    zipf.write(file_path, relative_path)
                    file_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Erro ao adicionar {relative_path}: {e}')
                    )

        self.stdout.write(f'📁 {file_count} arquivos adicionados ao backup')

    def add_remote_files_to_zip(self, zipf):
        """Adiciona arquivos remotos ao ZIP (implementação básica)"""
        self.stdout.write(
            self.style.WARNING('⚠️  Backup de storage remoto não implementado completamente')
        )
        self.stdout.write('💡 Considere usar ferramentas específicas do seu provider (AWS CLI, etc.)')

    def restore_backup(self, backup_filename, backup_dir):
        """Restaura backup dos arquivos de mídia"""
        backup_path = os.path.join(backup_dir, backup_filename)

        if not os.path.exists(backup_path):
            raise CommandError(f'Backup não encontrado: {backup_path}')

        self.stdout.write(
            self.style.WARNING('⚠️  ATENÇÃO: Esta operação irá substituir arquivos existentes!')
        )
        response = input('Digite "CONFIRMAR" para continuar: ')
        if response != 'CONFIRMAR':
            self.stdout.write('❌ Restauração cancelada')
            return

        try:
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            os.makedirs(media_root, exist_ok=True)

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                file_count = 0
                for file_info in zipf.infolist():
                    try:
                        # Extrair arquivo
                        zipf.extract(file_info, media_root)
                        file_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Erro ao extrair {file_info.filename}: {e}')
                        )

            self.stdout.write(
                self.style.SUCCESS(f'✅ Backup restaurado com sucesso!')
            )
            self.stdout.write(f'📁 {file_count} arquivos restaurados')

        except Exception as e:
            raise CommandError(f'Erro ao restaurar backup: {e}')

    def list_backups(self, backup_dir):
        """Lista backups disponíveis"""
        if not os.path.exists(backup_dir):
            self.stdout.write(
                self.style.WARNING('📁 Diretório de backup não encontrado')
            )
            return

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('media_backup_') and filename.endswith('.zip'):
                file_path = os.path.join(backup_dir, filename)
                file_size = os.path.getsize(file_path)
                file_time = os.path.getmtime(file_path)
                
                backups.append({
                    'filename': filename,
                    'size': file_size,
                    'time': file_time
                })

        if not backups:
            self.stdout.write(
                self.style.WARNING('📁 Nenhum backup encontrado')
            )
            return

        # Ordenar por data (mais recente primeiro)
        backups.sort(key=lambda x: x['time'], reverse=True)

        self.stdout.write(
            self.style.SUCCESS('📦 Backups disponíveis:\n')
        )

        for i, backup in enumerate(backups, 1):
            size_mb = backup['size'] / (1024 * 1024)
            date_str = datetime.fromtimestamp(backup['time']).strftime('%d/%m/%Y %H:%M:%S')
            
            self.stdout.write(f'  {i}. {backup["filename"]}')
            self.stdout.write(f'     📅 Data: {date_str}')
            self.stdout.write(f'     📊 Tamanho: {size_mb:.2f} MB')
            self.stdout.write('')
