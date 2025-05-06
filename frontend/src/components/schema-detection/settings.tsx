"use client";

import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel } from "@/components/ui/form"
import { useForm } from "react-hook-form"
import { Switch } from "@/components/ui/switch"
import { useStore } from "@/lib/store"
import { useTheme } from "@/components/theme-provider"
import { toast } from "sonner"
import { useEffect } from "react"

interface SettingsFormValues {
  detectRelations: boolean
  inferTypes: boolean
  generateNullableFields: boolean
  generateIndexes: boolean
  darkMode: boolean
}

export function Settings() {
  const { settings, updateSettings } = useStore()
  const { setTheme } = useTheme()
  
  const form = useForm<SettingsFormValues>({
    defaultValues: settings
  })

  // Update form when settings change
  useEffect(() => {
    form.reset(settings)
  }, [settings, form])

  // Handle setting changes immediately
  const handleSettingChange = (data: Partial<SettingsFormValues>) => {
    updateSettings({ ...settings, ...data })
    // If darkMode is being changed, also update the theme
    if ('darkMode' in data) {
      setTheme(data.darkMode ? 'dark' : 'light')
    }
    toast.success('Setting updated')
  }

  return (
    <Form {...form}>
      <div className="space-y-6">
        <FormField
          control={form.control}
          name="detectRelations"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Detect Relations</FormLabel>
                <FormDescription>
                  Automatically detect and generate relationships between tables
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={(checked) => {
                    field.onChange(checked)
                    handleSettingChange({ detectRelations: checked })
                  }}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="inferTypes"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Infer Types</FormLabel>
                <FormDescription>
                  Automatically infer field types from data patterns
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={(checked) => {
                    field.onChange(checked)
                    handleSettingChange({ inferTypes: checked })
                  }}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="generateNullableFields"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Generate Nullable Fields</FormLabel>
                <FormDescription>
                  Mark fields as nullable when not all records contain values
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={(checked) => {
                    field.onChange(checked)
                    handleSettingChange({ generateNullableFields: checked })
                  }}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="generateIndexes"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Generate Indexes</FormLabel>
                <FormDescription>
                  Automatically generate database indexes for common query patterns
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={(checked) => {
                    field.onChange(checked)
                    handleSettingChange({ generateIndexes: checked })
                  }}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="darkMode"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Dark Mode</FormLabel>
                <FormDescription>
                  Toggle dark mode for the application interface
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={(checked) => {
                    field.onChange(checked)
                    handleSettingChange({ darkMode: checked })
                  }}
                />
              </FormControl>
            </FormItem>
          )}
        />
      </div>
    </Form>
  )
}