from anthropic import Anthropic
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ClaudeAnalyzer:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 8000):
        """Initialize Claude API client"""
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    async def analyze_vm(self, vm_data: Dict, cluster_context: Optional[Dict] = None) -> Dict:
        """
        Analyze a single VM/LXC and generate comprehensive documentation and templates
        """
        vm_config = json.dumps(vm_data["config"], indent=2)
        context = json.dumps(cluster_context, indent=2) if cluster_context else "No cluster context provided"

        prompt = f"""You are analyzing a Proxmox virtual machine/container as part of a comprehensive infrastructure audit.

VM/LXC Details:
- ID: {vm_data["vm_id"]}
- Name: {vm_data["vm_name"]}
- Type: {vm_data["vm_type"]}
- Node: {vm_data["node"]}
- Status: {vm_data["status"]}

Configuration:
{vm_config}

Cluster Context:
{context}

Please provide a comprehensive analysis including:

1. **Purpose and Role**: What this VM/LXC appears to be used for
2. **Resource Allocation**: CPU, memory, disk, network configuration assessment
3. **Key Services**: Identified services and applications
4. **Dependencies**: Potential dependencies on other infrastructure
5. **Configuration Quality**: Assessment of configuration best practices

Keep this analysis concise but thorough (2-3 paragraphs)."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return {"analysis": response.content[0].text}
        except Exception as e:
            logger.error(f"Error analyzing VM {vm_data['vm_id']}: {e}")
            return {"analysis": f"Error during analysis: {str(e)}"}

    async def security_review(self, vm_data: Dict) -> Dict:
        """Generate security review for a VM/LXC"""
        vm_config = json.dumps(vm_data["config"], indent=2)

        prompt = f"""Perform a security review of this Proxmox VM/LXC configuration:

Type: {vm_data["vm_type"]}
Name: {vm_data["vm_name"]}

Configuration:
{vm_config}

Provide a security assessment covering:

1. **Network Security**: Firewall settings, network isolation, exposed services
2. **Resource Limits**: CPU/memory limits for DoS prevention
3. **Storage Security**: Disk encryption, backup configuration
4. **Access Control**: User permissions, SSH configuration if visible
5. **Security Recommendations**: Prioritized list of security improvements

Format as a structured report with clear action items."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return {"security_review": response.content[0].text}
        except Exception as e:
            logger.error(f"Error in security review for {vm_data['vm_id']}: {e}")
            return {"security_review": f"Error during security review: {str(e)}"}

    async def optimization_recommendations(self, vm_data: Dict) -> Dict:
        """Generate optimization recommendations"""
        vm_config = json.dumps(vm_data["config"], indent=2)

        prompt = f"""Analyze this Proxmox VM/LXC for optimization opportunities:

Type: {vm_data["vm_type"]}
Name: {vm_data["vm_name"]}
Status: {vm_data["status"]}

Configuration:
{vm_config}

Provide optimization recommendations for:

1. **Resource Optimization**: CPU, memory, and disk allocation improvements
2. **Performance**: Configuration changes for better performance
3. **Cost Efficiency**: Ways to reduce resource usage without impacting functionality
4. **Reliability**: Improvements for stability and uptime
5. **Modern Best Practices**: Updates to use current Proxmox features

Provide concrete, actionable recommendations with expected benefits."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return {"optimization_recommendations": response.content[0].text}
        except Exception as e:
            logger.error(f"Error generating optimizations for {vm_data['vm_id']}: {e}")
            return {"optimization_recommendations": f"Error generating optimizations: {str(e)}"}

    async def generate_terraform(self, vm_data: Dict) -> Dict:
        """Generate Terraform template for VM/LXC"""
        vm_config = json.dumps(vm_data["config"], indent=2)

        prompt = f"""Generate a Terraform template using the Telmate/proxmox provider to recreate this VM/LXC:

Type: {vm_data["vm_type"]}
Name: {vm_data["vm_name"]}
Node: {vm_data["node"]}

Current Configuration:
{vm_config}

Generate:
1. A complete Terraform resource definition
2. Variable definitions for configurable parameters
3. Output values for important attributes
4. Brief comments explaining key configurations

Use the appropriate resource type:
- For QEMU VMs: proxmox_vm_qemu
- For LXC: proxmox_lxc

Make the template reusable and follow Terraform best practices."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return {"terraform_template": response.content[0].text}
        except Exception as e:
            logger.error(f"Error generating Terraform for {vm_data['vm_id']}: {e}")
            return {"terraform_template": f"# Error generating Terraform: {str(e)}"}

    async def generate_ansible(self, vm_data: Dict) -> Dict:
        """Generate Ansible playbook for VM/LXC"""
        vm_config = json.dumps(vm_data["config"], indent=2)

        prompt = f"""Generate an Ansible playbook to provision and configure this VM/LXC:

Type: {vm_data["vm_type"]}
Name: {vm_data["vm_name"]}

Configuration:
{vm_config}

Generate:
1. Ansible playbook for creating/configuring the VM/LXC
2. Variable definitions
3. Tasks for common setup based on the configuration
4. Handlers if needed

Use the community.general.proxmox module for QEMU VMs or community.general.proxmox_lxc for containers.
Include basic post-creation configuration tasks where applicable."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return {"ansible_playbook": response.content[0].text}
        except Exception as e:
            logger.error(f"Error generating Ansible for {vm_data['vm_id']}: {e}")
            return {"ansible_playbook": f"# Error generating Ansible: {str(e)}"}

    async def generate_infrastructure_summary(self, all_analyses: list, cluster_info: Dict) -> str:
        """Generate comprehensive infrastructure summary report"""
        summary_data = {
            "total_resources": len(all_analyses),
            "vms": len([a for a in all_analyses if a.get("vm_type") == "qemu"]),
            "lxcs": len([a for a in all_analyses if a.get("vm_type") == "lxc"]),
            "nodes": cluster_info.get("nodes", [])
        }

        prompt = f"""Generate a comprehensive infrastructure summary report for a Proxmox cluster.

Cluster Overview:
- Total VMs/LXCs: {summary_data['total_resources']}
- QEMU VMs: {summary_data['vms']}
- LXC Containers: {summary_data['lxcs']}
- Nodes: {', '.join(summary_data['nodes'])}

Create an executive summary covering:

1. **Infrastructure Overview**: High-level architecture and organization
2. **Key Findings**: Important patterns, issues, or opportunities discovered
3. **Security Posture**: Overall security status and critical concerns
4. **Optimization Opportunities**: Major efficiency improvements possible
5. **Standardization Recommendations**: Ways to improve consistency
6. **Next Steps**: Prioritized action plan for infrastructure improvements

This is for a comprehensive infrastructure audit. Be thorough but concise."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating infrastructure summary: {e}")
            return f"Error generating summary: {str(e)}"

    async def analyze_complete(self, vm_data: Dict, cluster_context: Optional[Dict] = None,
                               include_security: bool = True, include_optimization: bool = True,
                               include_terraform: bool = True, include_ansible: bool = True) -> Dict:
        """
        Perform complete analysis of a VM/LXC including all optional components
        """
        results = {}

        # Base analysis (always included)
        analysis_result = await self.analyze_vm(vm_data, cluster_context)
        results.update(analysis_result)

        # Optional analyses
        if include_security:
            security_result = await self.security_review(vm_data)
            results.update(security_result)

        if include_optimization:
            optimization_result = await self.optimization_recommendations(vm_data)
            results.update(optimization_result)

        if include_terraform:
            terraform_result = await self.generate_terraform(vm_data)
            results.update(terraform_result)

        if include_ansible:
            ansible_result = await self.generate_ansible(vm_data)
            results.update(ansible_result)

        return results
