"""Management command to analyze and suggest new TRELLIS clusters."""

from django.core.management.base import BaseCommand
from apps.documentos.trellis_clustering import TRELLISClusteringService

class Command(BaseCommand):
    help = 'Analyze TRELLIS interactions and suggest new clusters'
    
    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', type=str, required=True)
        parser.add_argument('--min-samples', type=int, default=5)
    
    def handle(self, *args, **options):
        service = TRELLISClusteringService()
        
        discovered = service.analyze_unclustered_interactions(
            tenant_id=options['tenant_id'],
            min_samples=options['min_samples']
        )
        
        self.stdout.write(f"\nDiscovered {len(discovered)} potential clusters:\n")
        
        for i, cluster in enumerate(discovered, 1):
            self.stdout.write(f"\n{i}. {cluster['suggested_id']}")
            self.stdout.write(f"   Sample count: {cluster['sample_count']}")
            self.stdout.write(f"   Pattern: {cluster['pattern']}")
            self.stdout.write(f"   Act type: {cluster['act_type']}")
            self.stdout.write(f"   Samples:")
            for cmd in cluster['sample_commands'][:3]:
                self.stdout.write(f"     - {cmd}")
            
            # Generate parser code
            parser_code = service.suggest_deterministic_parser(cluster['suggested_id'])
            self.stdout.write(f"\n   Suggested parser:\n{parser_code}\n")
