from proxmoxer import ProxmoxAPI
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ProxmoxClient:
    def __init__(self, host: str, user: str, password: str = None,
                 token_name: str = None, token_value: str = None, verify_ssl: bool = False):
        """Initialize Proxmox API client"""
        self.host = host

        if token_name and token_value:
            # Use API token authentication
            self.proxmox = ProxmoxAPI(
                host,
                user=user,
                token_name=token_name,
                token_value=token_value,
                verify_ssl=verify_ssl
            )
        elif password:
            # Use password authentication
            self.proxmox = ProxmoxAPI(
                host,
                user=user,
                password=password,
                verify_ssl=verify_ssl
            )
        else:
            raise ValueError("Either password or token credentials must be provided")

    def get_all_nodes(self) -> List[str]:
        """Get all nodes in the cluster"""
        try:
            nodes = self.proxmox.nodes.get()
            return [node['node'] for node in nodes]
        except Exception as e:
            logger.error(f"Error fetching nodes: {e}")
            return []

    def get_all_vms(self) -> List[Dict]:
        """Get all VMs (QEMU) from all nodes"""
        all_vms = []
        nodes = self.get_all_nodes()

        for node in nodes:
            try:
                vms = self.proxmox.nodes(node).qemu.get()
                for vm in vms:
                    vm_detail = {
                        "node": node,
                        "vm_id": str(vm["vmid"]),
                        "vm_name": vm.get("name", f"VM-{vm['vmid']}"),
                        "vm_type": "qemu",
                        "status": vm.get("status", "unknown"),
                        "config": self.get_vm_config(node, vm["vmid"])
                    }
                    all_vms.append(vm_detail)
            except Exception as e:
                logger.error(f"Error fetching VMs from node {node}: {e}")

        return all_vms

    def get_all_lxcs(self) -> List[Dict]:
        """Get all LXC containers from all nodes"""
        all_lxcs = []
        nodes = self.get_all_nodes()

        for node in nodes:
            try:
                lxcs = self.proxmox.nodes(node).lxc.get()
                for lxc in lxcs:
                    lxc_detail = {
                        "node": node,
                        "vm_id": str(lxc["vmid"]),
                        "vm_name": lxc.get("name", f"LXC-{lxc['vmid']}"),
                        "vm_type": "lxc",
                        "status": lxc.get("status", "unknown"),
                        "config": self.get_lxc_config(node, lxc["vmid"])
                    }
                    all_lxcs.append(lxc_detail)
            except Exception as e:
                logger.error(f"Error fetching LXCs from node {node}: {e}")

        return all_lxcs

    def get_all_resources(self) -> List[Dict]:
        """Get all VMs and LXCs from the entire cluster"""
        vms = self.get_all_vms()
        lxcs = self.get_all_lxcs()
        return vms + lxcs

    def get_vm_config(self, node: str, vmid: int) -> Dict:
        """Get detailed configuration for a VM"""
        try:
            config = self.proxmox.nodes(node).qemu(vmid).config.get()
            return config
        except Exception as e:
            logger.error(f"Error fetching VM config for {vmid} on {node}: {e}")
            return {}

    def get_lxc_config(self, node: str, vmid: int) -> Dict:
        """Get detailed configuration for an LXC container"""
        try:
            config = self.proxmox.nodes(node).lxc(vmid).config.get()
            return config
        except Exception as e:
            logger.error(f"Error fetching LXC config for {vmid} on {node}: {e}")
            return {}

    def get_cluster_info(self) -> Dict:
        """Get overall cluster information"""
        try:
            cluster_status = self.proxmox.cluster.status.get()
            cluster_resources = self.proxmox.cluster.resources.get()

            return {
                "status": cluster_status,
                "resources": cluster_resources,
                "nodes": self.get_all_nodes()
            }
        except Exception as e:
            logger.error(f"Error fetching cluster info: {e}")
            return {}
