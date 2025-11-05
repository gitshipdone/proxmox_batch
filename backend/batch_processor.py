import asyncio
import logging
from typing import Dict, List
from pathlib import Path
import json

from proxmox_client import ProxmoxClient
from claude_analyzer import ClaudeAnalyzer
from database import Database
from config import settings

logger = logging.getLogger(__name__)


class BatchProcessor:
    def __init__(self, proxmox_client: ProxmoxClient, claude_analyzer: ClaudeAnalyzer, database: Database):
        self.proxmox = proxmox_client
        self.claude = claude_analyzer
        self.db = database
        self.output_dir = Path(settings.output_dir)
        self.output_dir.mkdir(exist_ok=True)

    async def process_single_vm(self, vm_data: Dict, cluster_context: Dict = None) -> Dict:
        """Process a single VM/LXC with complete analysis"""
        logger.info(f"Processing {vm_data['vm_type']} {vm_data['vm_name']} (ID: {vm_data['vm_id']})")

        try:
            analysis_results = await self.claude.analyze_complete(
                vm_data=vm_data,
                cluster_context=cluster_context,
                include_security=settings.enable_security_review,
                include_optimization=settings.enable_optimization,
                include_terraform=settings.enable_terraform,
                include_ansible=settings.enable_ansible
            )

            # Merge results with VM data
            result = {**vm_data, **analysis_results}

            return result

        except Exception as e:
            logger.error(f"Error processing VM {vm_data['vm_id']}: {e}")
            return {
                **vm_data,
                "analysis": f"Error: {str(e)}",
                "error": True
            }

    async def process_batch(self, vms: List[Dict], cluster_context: Dict = None) -> List[Dict]:
        """Process a batch of VMs/LXCs concurrently"""
        tasks = [self.process_single_vm(vm, cluster_context) for vm in vms]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
            else:
                processed_results.append(result)

        return processed_results

    async def run_full_analysis(self) -> int:
        """
        Run complete analysis of entire Proxmox infrastructure
        Returns the batch job ID
        """
        logger.info("Starting full infrastructure analysis")

        # Get cluster information
        cluster_info = self.proxmox.get_cluster_info()
        logger.info(f"Cluster has {len(cluster_info.get('nodes', []))} nodes")

        # Get all VMs and LXCs
        all_resources = self.proxmox.get_all_resources()
        logger.info(f"Found {len(all_resources)} total resources to analyze")

        if not all_resources:
            logger.warning("No resources found to analyze")
            return None

        # Create batch job in database
        job_id = await self.db.create_batch_job(len(all_resources))
        logger.info(f"Created batch job {job_id}")

        # Create job-specific output directory
        job_output_dir = self.output_dir / f"job_{job_id}"
        job_output_dir.mkdir(exist_ok=True)

        try:
            # Process resources in batches
            batch_size = settings.batch_size
            all_results = []
            processed_count = 0

            for i in range(0, len(all_resources), batch_size):
                batch = all_resources[i:i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} resources)")

                batch_results = await self.process_batch(batch, cluster_info)
                all_results.extend(batch_results)

                # Save each VM analysis to database
                for result in batch_results:
                    await self.db.save_vm_analysis(job_id, result)

                processed_count += len(batch_results)
                await self.db.update_batch_job(job_id, processed_count)

                logger.info(f"Completed {processed_count}/{len(all_resources)} resources")

            # Generate individual files for each VM/LXC
            await self.save_individual_outputs(job_id, all_results, job_output_dir)

            # Generate infrastructure summary
            logger.info("Generating infrastructure summary report")
            summary = await self.claude.generate_infrastructure_summary(all_results, cluster_info)
            await self.db.save_infrastructure_report(job_id, "summary", summary)

            # Save summary to file
            summary_file = job_output_dir / "infrastructure_summary.md"
            summary_file.write_text(summary)

            # Generate consolidated outputs
            await self.generate_consolidated_outputs(job_id, all_results, job_output_dir)

            # Mark job as completed
            await self.db.update_batch_job(job_id, processed_count, status="completed")
            logger.info(f"Batch job {job_id} completed successfully")

            return job_id

        except Exception as e:
            logger.error(f"Error during batch processing: {e}")
            await self.db.update_batch_job(job_id, processed_count, status="failed", error=str(e))
            raise

    async def save_individual_outputs(self, job_id: int, results: List[Dict], output_dir: Path):
        """Save individual files for each VM/LXC"""
        logger.info("Saving individual VM/LXC outputs")

        for result in results:
            vm_name = result['vm_name'].replace(' ', '_').replace('/', '_')
            vm_dir = output_dir / f"{result['vm_type']}_{vm_name}_{result['vm_id']}"
            vm_dir.mkdir(exist_ok=True)

            # Save analysis
            if result.get('analysis'):
                (vm_dir / "analysis.md").write_text(result['analysis'])

            # Save security review
            if result.get('security_review'):
                (vm_dir / "security_review.md").write_text(result['security_review'])

            # Save optimization recommendations
            if result.get('optimization_recommendations'):
                (vm_dir / "optimization_recommendations.md").write_text(result['optimization_recommendations'])

            # Save Terraform template
            if result.get('terraform_template'):
                (vm_dir / "main.tf").write_text(result['terraform_template'])

            # Save Ansible playbook
            if result.get('ansible_playbook'):
                (vm_dir / "playbook.yml").write_text(result['ansible_playbook'])

            # Save raw configuration
            (vm_dir / "config.json").write_text(json.dumps(result['config'], indent=2))

    async def generate_consolidated_outputs(self, job_id: int, results: List[Dict], output_dir: Path):
        """Generate consolidated Terraform and Ansible files"""
        logger.info("Generating consolidated IaC templates")

        # Consolidated Terraform
        if settings.enable_terraform:
            terraform_dir = output_dir / "terraform"
            terraform_dir.mkdir(exist_ok=True)

            # Main file with all resources
            main_tf_content = "# Proxmox Infrastructure - Generated by Proxmox Batch Processor\n\n"
            main_tf_content += """terraform {
  required_providers {
    proxmox = {
      source  = "Telmate/proxmox"
      version = "~> 2.9"
    }
  }
}

provider "proxmox" {
  pm_api_url      = var.proxmox_api_url
  pm_api_token_id = var.proxmox_api_token_id
  pm_api_token_secret = var.proxmox_api_token_secret
  pm_tls_insecure = true
}

"""

            for result in results:
                if result.get('terraform_template'):
                    main_tf_content += f"\n# {result['vm_name']} ({result['vm_id']})\n"
                    main_tf_content += result['terraform_template'] + "\n\n"

            (terraform_dir / "main.tf").write_text(main_tf_content)

            # Variables file
            variables_tf = """variable "proxmox_api_url" {
  description = "Proxmox API URL"
  type        = string
}

variable "proxmox_api_token_id" {
  description = "Proxmox API Token ID"
  type        = string
}

variable "proxmox_api_token_secret" {
  description = "Proxmox API Token Secret"
  type        = string
  sensitive   = true
}
"""
            (terraform_dir / "variables.tf").write_text(variables_tf)

            # README
            readme = """# Proxmox Infrastructure - Terraform

This directory contains generated Terraform configurations for your Proxmox infrastructure.

## Usage

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Review the plan:
   ```bash
   terraform plan
   ```

3. Apply (when ready):
   ```bash
   terraform apply
   ```

## Configuration

Set the following variables in `terraform.tfvars` or via environment variables:
- `proxmox_api_url`
- `proxmox_api_token_id`
- `proxmox_api_token_secret`
"""
            (terraform_dir / "README.md").write_text(readme)

        # Consolidated Ansible
        if settings.enable_ansible:
            ansible_dir = output_dir / "ansible"
            ansible_dir.mkdir(exist_ok=True)

            # Main playbook
            playbook_content = """---
# Proxmox Infrastructure - Generated by Proxmox Batch Processor
- name: Provision Proxmox Infrastructure
  hosts: localhost
  gather_facts: false
  tasks:

"""

            for i, result in enumerate(results):
                if result.get('ansible_playbook'):
                    playbook_content += f"    # {result['vm_name']} ({result['vm_id']})\n"
                    # Extract tasks from the generated playbook (simplified)
                    playbook_content += f"    # See individual playbooks for details\n\n"

            (ansible_dir / "site.yml").write_text(playbook_content)

            # Save individual playbooks
            playbooks_dir = ansible_dir / "playbooks"
            playbooks_dir.mkdir(exist_ok=True)

            for result in results:
                if result.get('ansible_playbook'):
                    vm_name = result['vm_name'].replace(' ', '_').replace('/', '_')
                    playbook_file = playbooks_dir / f"{vm_name}_{result['vm_id']}.yml"
                    playbook_file.write_text(result['ansible_playbook'])

            # README
            readme = """# Proxmox Infrastructure - Ansible

This directory contains generated Ansible playbooks for your Proxmox infrastructure.

## Usage

1. Install required collections:
   ```bash
   ansible-galaxy collection install community.general
   ```

2. Configure inventory and variables in `inventory/hosts.yml`

3. Run playbooks:
   ```bash
   ansible-playbook -i inventory/hosts.yml playbooks/<specific-playbook>.yml
   ```

## Organization

- `playbooks/`: Individual playbooks for each VM/LXC
- `site.yml`: Main playbook (customize as needed)
"""
            (ansible_dir / "README.md").write_text(readme)

        logger.info("Consolidated outputs generated successfully")
