term.setBackgroundColor(colors.black)
term.setTextColor(colors.white)
term.clear()
term.setCursorPos(1,1)
print("LevelOS - Multimonitor Demo")
print("Time: " .. textutils.formatTime(os.time(), true))
print("Press Ctrl+T to exit")
while true do
  os.pullEvent()
end
