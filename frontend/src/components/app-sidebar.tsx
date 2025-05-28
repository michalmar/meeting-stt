import * as React from "react"
import {
  AudioLines,
  BookOpen,
  Frame,
  Map,
  PieChart,
  Settings2,
  SquareTerminal,
} from "lucide-react"
import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem
} from "@/components/ui/sidebar"
import { useUserContext } from "@/contexts/UserContext"
import h1 from '@/assets/h1.png'


interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  // Removed onUserNameChange prop
}

const data = {
  user: {
    name: "Jon Doe",
    email: "johne@microsoft.com",
    avatar: h1,
  },
  navMain: [
    {
      title: "Home",
      url: "/",
      icon: SquareTerminal,
      isActive: true,
      items: [
        { title: "Transcriber", url: "/" },
        
      ],
    },
    {
      title: "Documentation",
      url: "#",
      icon: BookOpen,
      isActive: true,
      items: [
        {
          title: "Introduction",
          url: "/introduction",
        },
        
      ],
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
      isActive: true,
      items: [
        {
          title: "General",
          url: "/general",
        },
      ],
    },
  ],
  projects: [
    { name: "Design Engineering", url: "#", icon: Frame },
    { name: "Sales & Marketing", url: "#", icon: PieChart },
    { name: "Travel", url: "#", icon: Map },
  ],
}

export function AppSidebar({
  ...sidebarProps
}: AppSidebarProps) {
  const { userInfo } = useUserContext();


  return (
    <Sidebar collapsible="icon" {...sidebarProps}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild className="">
              <a href="#">
                <AudioLines className="h-8 w-12" />
                <span className="text-base font-semibold">Transcriber</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={userInfo} />
      </SidebarFooter>
    </Sidebar>
  );
}