import { AppSidebar } from "@/components/app-sidebar"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from '@/components/mode-toggle'

import { Footer } from '@/components/Footer'

import { Card, CardHeader,CardContent, CardFooter} from "@/components/ui/card"
import { AlarmClock } from 'lucide-react'

export default function Introduction() {

  return (
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <SidebarProvider defaultOpen={true}>
        <AppSidebar />
        <SidebarInset>
          <header className="flex sticky top-0 bg-background h-10 shrink-0 items-center gap-2 border-b px-4 z-10 shadow">
            <div className="flex items-center gap-2 px-4 w-full">
              {/* <img src={banner} alt="Banner" className="h-64" /> */}
              <SidebarTrigger className="-ml-1" />
              {/* <Bot className="h-8 w-8" /> */}
              {/* <img src={appLogo  } alt="Banner" className="h-8" /> */}
              
              <Separator orientation="vertical" className="mr-2 h-4" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="#">
                      App
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbPage>Introduction</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
              <div className="ml-auto hidden items-center gap-2 md:flex">
              <ModeToggle />
              </div>
            </div>
          </header>
          {/* Main content */}
         
          <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
            <div className="min-h-[100vh] flex-1 rounded-xl bg-muted/50 md:min-h-min">
              <Separator className="mb-4" />
              <Card className={`md:col-span-2 h-full flex flex-col`}>
                <CardHeader>
                  <AlarmClock className="h-8 w-8" />
                </CardHeader>
                <CardContent className="flex-1">
                  <h2 className="text-lg font-bold">Comming soon...</h2>
                  <p>
                    This is a placeholder for the Introduction documentation page.
                    The content will be updated soon.
                  </p>
                </CardContent>
                <CardFooter>
                  <p className="text-sm text-muted-foreground">
                    AI-generated content may be incorrect.
                  </p>
                </CardFooter>
              </Card>
            </div>
          </div>
          {/* Footer */}
          <Footer />
        </SidebarInset>
      </SidebarProvider>
    </ThemeProvider>
  );
}
