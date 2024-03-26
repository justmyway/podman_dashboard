from pyVim import connect
from pyVmomi import vim

from concurrent.futures import ThreadPoolExecutor
import getpass
import time

def get_folder(service_instance, folder_name):
    # Get the root folder object
    root_folder = service_instance.content.rootFolder

    # Find the folder object with the given name
    for child in root_folder.childEntity:
        if child.name == folder_name and isinstance(child, vim.Folder):
            return child

    print(f"Folder '{folder_name}' not found.")

    return root_folder

def get_datastore(service_instance, datastore_name):
    try:
        # Get the root folder
        content = service_instance.RetrieveContent()
        root_folder = content.rootFolder

        # Search for the datastore by name
        datastore_view = content.viewManager.CreateContainerView(
            container=root_folder,
            type=[vim.Datastore],
            recursive=True
        )
        datastore_list = datastore_view.view

        for datastore in datastore_list:
            if datastore.name == datastore_name:
                return datastore

        return None

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def check_vm_exists(service_instance, vm_name):
    try:
        # Get the root folder
        content = service_instance.RetrieveContent()
        root_folder = content.rootFolder

        # Search for the VM by name
        vm_view = content.viewManager.CreateContainerView(
            container=root_folder,
            type=[vim.VirtualMachine],
            recursive=True
        )
        vm_list = vm_view.view

        for vm in vm_list:
            if vm.name == vm_name:
                return True

        return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
def return_vm_object(service_instance, vm_name):
    try:
        # Get the root folder
        content = service_instance.RetrieveContent()
        root_folder = content.rootFolder

        # Search for the VM by name
        vm_view = content.viewManager.CreateContainerView(
            container=root_folder,
            type=[vim.VirtualMachine],
            recursive=True
        )
        vm_list = vm_view.view

        for vm in vm_list:
            if vm.name == vm_name:
                return vm

        return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
def clone_vm(service_instance, root_folder, template_name, clone_vm_name):
    # Get the template VM object
    template_vm = return_vm_object(service_instance, template_name)

    if template_vm is None:
        print(f"Template VM '{template_name}' not found.")
        return

    # Clone the template VM
    try:
        target_datastore = get_datastore(service_instance, datastore_name)

        relocate_spec = vim.vm.RelocateSpec()
        relocate_spec.datastore = target_datastore

        clone_spec = vim.vm.CloneSpec(powerOn=True, location=relocate_spec)
        clone_task = template_vm.Clone(folder=root_folder, name=clone_vm_name, spec=clone_spec)
        print(f"Cloning VM '{template_name}' to '{clone_vm_name}'...")

        # Wait for the clone task to complete
        while clone_task.info.state == vim.TaskInfo.State.running:
            time.sleep(1)

        if clone_task.info.state == vim.TaskInfo.State.success:
            print(f"VM '{clone_vm_name}' cloned successfully.")
            return True
        else:
            print(f"Failed to clone VM '{clone_vm_name}'.")
            return False
    except Exception as e:
        print(f"Error cloning VM: {str(e)}")
        return False

def power_on_vm(vm):
    if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOn:
        try:
            task = vm.PowerOn()
            print(f"Powering on VM '{vm.name}'...")

            # Wait for the task to complete
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(1)

            if task.info.state == vim.TaskInfo.State.success:
                print(f"VM '{vm.name}' powered on successfully.")
            else:
                print(f"Failed to power on VM '{vm.name}'.")
        except Exception as e:
            print(f"Error powering on VM: {str(e)}")
    else:
        print(f"VM '{vm.name}' is already powered on.")

def wait_for_ip_address(vm):
    max_wait_time = 600  # Maximum wait time in seconds (10 minutes)
    local_start_time = time.time()

    while True:
        if vm.guest.ipAddress:
            return vm.guest.ipAddress

        if time.time() - local_start_time >= max_wait_time:
            print("Timeout: Failed to get IP address within the specified time.")
            return None

        time.sleep(1)

def shutdown_vm(vm):
    if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
        try:
            task = vm.PowerOff()
            print(f"Shutting down VM '{vm.name}'...")

            # Wait for the task to complete
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(1)

            if task.info.state == vim.TaskInfo.State.success:
                print(f"VM '{vm.name}' shut down successfully.")
            else:
                print(f"Failed to shut down VM '{vm.name}'.")
        except Exception as e:
            print(f"Error shutting down VM: {str(e)}")
    else:
        print(f"VM '{vm.name}' is already powered off.")

def remove_vm(vm):
    # Power off the VM if it is powered on
    if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
        shutdown_vm(vm)

    # Delete the VM
    try:
        task = vm.Destroy()
        print(f"Deleting VM '{vm_name}'...")

        # Wait for the task to complete
        while task.info.state == vim.TaskInfo.State.running:
            time.sleep(1)

        if task.info.state == vim.TaskInfo.State.success:
            print(f"VM '{vm_name}' deleted successfully.")
            return True
        else:
            print(f"Failed to delete VM '{vm_name}'.")
            return False
    except Exception as e:
        print(f"Error deleting VM: {str(e)}")
        return False

def life_cycle_vm(service_instance, vm_name):
    # Check if the VM exists
    if check_vm_exists(service_instance, vm_name):
        print(f"VM '{vm_name}' does exist.")
        return

    # Clone the VM
    clone_vm(service_instance, root_folder, template_name, vm_name)

    # Get the VM object
    vm = return_vm_object(service_instance, vm_name)

    if vm is None:
        print(f"VM '{vm_name}' not found.")
        return

    # Power on the VM
    power_on_vm(vm)

    # Wait for the VM to get an IP address
    ipadress = wait_for_ip_address(vm)
    print(f"VM '{vm_name}' IP address: {ipadress}")

    # Shutdown the VM
    shutdown_vm(vm)

    # Remove the VM
    remove_vm(vm)

    return True


# Usage example
host            = "vcenter.example.com"
username        = "my_username"
password        = getpass.getpass("Enter your password: ")

vm_names        = [f"vm_{i}" for i in range(1, 101)]
template_name   = ""
folder_name     = ""
datastore_name  = ""

# Connect to the vCenter server
service_instance = connect.SmartConnectNoSSL(
    host=host,
    user=username,
    pwd=password
)

# Get the vm folder
root_folder = get_folder(service_instance, folder_name)

# Start the timer
start_time = time.time()

# Create a thread pool executor
with ThreadPoolExecutor() as executor:
    # Submit the tasks to the executor
    results = [executor.submit(life_cycle_vm, service_instance, vm_name) for vm_name in vm_names]

    # Wait for the tasks to complete
    for result, vm_name in zip(results, vm_names):
        if result.result():
            print(f"VM '{vm_name}' exists.")
        else:
            print(f"VM '{vm_name}' does not exist.")



# Calculate the duration
duration = time.time() - start_time
print(f"Script duration: {duration} seconds")

# Disconnect from the vCenter server
connect.Disconnect(service_instance)