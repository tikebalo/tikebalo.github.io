local MonitorManager = {}

MonitorManager.monitors = {}

local function log(msg)
  print("[MonitorManager] " .. msg)
end

function MonitorManager.init(defaultProgram)
  for _, name in pairs(peripheral.getNames()) do
    if peripheral.getType(name) == "monitor" then
      MonitorManager.monitors[name] = {
        side = name,
        program = defaultProgram or "levelos.lua",
        args = {},
        role = "default",
      }
      log("Found monitor on " .. name)
    end
  end
end

local function runProgram(side, program, args)
  local mon = peripheral.wrap(side)
  if not mon then return end
  term.redirect(mon)
  mon.setCursorPos(1,1)
  mon.clear()
  local ok, err = pcall(function()
    shell.run("cc-os/" .. program, table.unpack(args or {}))
  end)
  term.redirect(term.native())
  if not ok then
    log("Error on " .. side .. ": " .. err)
    mon.setCursorPos(1,1)
    mon.write(err)
  end
end

function MonitorManager.monitorLoop(side)
  local info = MonitorManager.monitors[side]
  while true do
    if info.program then
      runProgram(side, info.program, info.args)
    end
    local ev = os.pullEvent()
    if ev == "monitor_update_" .. side then
      -- continue loop to restart program
    elseif ev == "monitor_close_" .. side then
      break
    end
  end
end

function MonitorManager.start(side)
  local info = MonitorManager.monitors[side]
  if not info then return end
  info.task = function() MonitorManager.monitorLoop(side) end
end

function MonitorManager.shell()
  while true do
    io.write("shell> ")
    local line = read()
    local args = {}
    for word in string.gmatch(line, "%S+") do table.insert(args, word) end
    local cmd = args[1]
    if cmd == "list" then
      for s, data in pairs(MonitorManager.monitors) do
        print(s .. " -> " .. (data.program or "<none>") .. " (" .. (data.role or "") .. ")")
      end
    elseif cmd == "switch" and args[2] and args[3] then
      local m = MonitorManager.monitors[args[2]]
      if m then
        m.program = args[3]
        m.args = { table.unpack(args,4) }
        os.queueEvent("monitor_update_"..args[2])
      else
        print("Unknown monitor: " .. args[2])
      end
    elseif cmd == "show" and args[2] and args[3] then
      local m = MonitorManager.monitors[args[2]]
      if m then
        m.program = "nfp_display.lua"
        m.args = { args[3] }
        os.queueEvent("monitor_update_"..args[2])
      else
        print("Unknown monitor: " .. args[2])
      end
    elseif cmd == "close" and args[2] then
      local m = MonitorManager.monitors[args[2]]
      if m then
        m.program = nil
        os.queueEvent("monitor_update_"..args[2])
      end
    elseif cmd == "reboot" and args[2] then
      local m = MonitorManager.monitors[args[2]]
      if m then
        os.queueEvent("monitor_update_"..args[2])
      end
    elseif cmd == "assign" and args[2] and args[3] then
      local m = MonitorManager.monitors[args[2]]
      if m then
        m.role = args[3]
      end
    elseif cmd == "exit" then
      break
    elseif cmd ~= "" then
      print("Unknown command: " .. cmd)
    end
  end
end

function MonitorManager.run()
  local tasks = {}
  for side in pairs(MonitorManager.monitors) do
    MonitorManager.start(side)
    table.insert(tasks, MonitorManager.monitors[side].task)
  end
  table.insert(tasks, MonitorManager.shell)
  parallel.waitForAny(table.unpack(tasks))
end

return MonitorManager
