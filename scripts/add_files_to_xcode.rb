#!/usr/bin/env ruby
# Add Swift files to Xcode project programmatically

require 'xcodeproj'

project_path = ARGV[0] || 'NeuroForgeApp/NeuroForgeApp.xcodeproj'
project = Xcodeproj::Project.open(project_path)

target = project.targets.first
sources_phase = target.source_build_phase

# Files to add
files_to_add = [
  'NeuroForgeApp/Sources/AthenaModels.swift',
  'NeuroForgeApp/Sources/AthenaState.swift',
  'NeuroForgeApp/Sources/VoiceManager.swift',
  'NeuroForgeApp/Sources/Notifications+App.swift',
  'NeuroForgeApp/Sources/AthenaDashboardView.swift',
  'NeuroForgeApp/Sources/Athena/CriticalAlertWindow.swift',
  'NeuroForgeApp/Sources/Athena/TribunalDecisionWindow.swift',
  'NeuroForgeApp/Sources/Athena/SystemEmergencyWindow.swift'
]

files_to_add.each do |file_path|
  file_ref = project.main_group.find_file_by_path(file_path)

  unless file_ref
    file_ref = project.main_group.new_reference(file_path)
  end

  unless sources_phase.files.find { |f| f.file_ref == file_ref }
    sources_phase.add_file_reference(file_ref)
    puts "✅ Added #{File.basename(file_path)}"
  else
    puts "⚠️  #{File.basename(file_path)} already in project"
  end
end

project.save
puts "\n✅ Project updated!"
