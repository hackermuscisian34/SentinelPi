
-- Enable DELETE for authenticated users on the devices table
create policy "devices_delete" on devices
  for delete using (auth.role() = 'authenticated');
