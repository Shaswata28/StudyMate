"use client";

import { useEffect, useState } from "react";

export default function ThemeControl() {
  const [theme, setTheme] = useState("system");

  useEffect(() => {
    setTheme(localStorage.getItem("studymate-theme") ?? "system");
  }, []);

  function changeTheme(value: string) {
    setTheme(value);
    localStorage.setItem("studymate-theme", value);
    window.dispatchEvent(new Event("studymate-theme"));
  }

  return (
    <fieldset className="grid grid-cols-3 gap-2 sm:gap-3">
      <legend className="sr-only">Color scheme</legend>
      {["system", "light", "dark"].map((option) => (
        <label key={option} className="relative block cursor-pointer">
          <input type="radio" name="appearance" value={option} checked={theme === option}
            onChange={() => changeTheme(option)} className="peer sr-only" />
          <span className="block rounded-control border border-line p-2 peer-checked:border-[#839071] peer-checked:ring-1 peer-checked:ring-[#839071] peer-focus-visible:outline peer-focus-visible:outline-offset-2 sm:p-3">
            <span aria-hidden className={`relative block h-12 overflow-hidden rounded-md border border-black/10 p-2 ${option === "dark" ? "bg-[#26241f]" : "bg-[#fffefb]"}`}>
              {option === "system" && <span className="absolute inset-y-0 right-0 w-1/2 bg-[#26241f]" />}
              <span className={`relative block h-1 w-2/5 rounded-full ${option === "dark" ? "bg-[#aeb296]" : "bg-[#858d74]"}`} />
            </span>
            <span className="mt-2 block text-center text-sm font-medium capitalize">{option}</span>
          </span>
        </label>
      ))}
    </fieldset>
  );
}
