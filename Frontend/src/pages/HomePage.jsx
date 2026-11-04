import {
  Chat,
  Channel,
  Window,
  MessageList,
  MessageInput,
  Thread,
  ChannelList,
} from "stream-chat-react";
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import { useStreamChat } from "../hooks/useStreamChat";
import PageLoader from "../components/PageLoader";
import { HashIcon, PlusIcon, UsersIcon, LogOutIcon } from "lucide-react";
import { clearSession } from "../lib/session";

import "../styles/stream-chat-theme.css";
import CreateChannelModal from "../components/CreateChannelModal";
import CustomChannelPreview from "../components/CustomChannelPreview";
import { PulseLoader } from "react-spinners";
import UsersList from "../components/UsersList";
import CustomChannelHeader from "../components/CustomChannelHeader";

const HomePage = ({ session, onLogout }) => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [activeChannel, setActiveChannel] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const { chatClient, isLoading, error } = useStreamChat(session);

  useEffect(() => {
    if (chatClient) {
      const channelId = searchParams.get("channel");
      if (channelId) {
        const channel = chatClient.channel("messaging", channelId);
        setActiveChannel(channel);
      }
    }
  }, [chatClient, searchParams]);

  if (error) {
    return <p>Something went wrong...</p>;
  }

  if (isLoading || !chatClient) return <PageLoader />;

  return (
    <div className="chat-wrapper">
      <Chat client={chatClient}>
        <div className="chat-container">
          {/* left sidebar*/}
          <div className="str-chat_channel-list">
            <div className="team-channel-list">
              {/* HEADER */}
              <div className="team-channel-list__header gap-4">
                <div className="brand-container">
                  <img src="/hello.png" alt="Logo" className="brand-logo" />
                  <span
                    className="text-4xl font-extrabold tracking-wide
                                        bg-gradient-to-br from-white via-neutral-300 to-white
                    bg-clip-text text-transparent
                    drop-shadow-[0_2px_10px_rgba(255,255,255,0.1)]
"
                  >
                    Fluent Meet
                  </span>
                </div>
                <div className="user-button-wrapper">
                  <button
                    title={`Signed in as ${session.name} — click to leave`}
                    className="flex items-center gap-1 text-sm text-white/80 hover:text-white cursor-pointer"
                    onClick={() => {
                      clearSession();
                      onLogout();
                    }}
                  >
                    <span className="truncate max-w-24">{session.name}</span>
                    <LogOutIcon className="size-4" />
                  </button>
                </div>
              </div>

              {/* {channels list}*/}
              <div className="team-channel-list_content">
                <div className="create-channel-section">
                  <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="create-channel-btn"
                  >
                    <PlusIcon className="size-4" />
                    <span>Create Channel</span>
                  </button>
                </div>

                {/* all the channels*/}
                <ChannelList
                  filters={{ members: { $in: [chatClient?.user?.id] } }}
                  options={{ state: true, watch: true }}
                  Preview={({ channel }) => (
                    <CustomChannelPreview
                      channel={channel}
                      activeChannel={activeChannel}
                      setActiveChannel={(channel) =>
                        setSearchParams({ channel: channel.id })
                      }
                    />
                  )}
                  List={({ children, loading, error }) => (
                    <div className="channel-sections">
                      <div className="section-header">
                        <div className="section-title">
                          <HashIcon className="size-4" />
                          <span>Channels</span>
                        </div>
                      </div>

                      {loading && (
                        <div className="loading-message">
                          <PulseLoader
                            color="#fff"
                            size={13}
                            speedMultiplier={0.7}
                          />
                        </div>
                      )}
                      {error && (
                        <div className="error-message">
                          Error while loading channels
                        </div>
                      )}
                      <div className="channels-list">{children}</div>

                      <div className="section-header direct-messages">
                        <div className="section-title">
                          <UsersIcon className="size-4" />
                          <span>Direct Messages</span>
                        </div>
                      </div>
                      <UsersList activeChannel={activeChannel} />
                    </div>
                  )}
                />
              </div>
            </div>
          </div>

          {/* {right-container}*/}
          <div className="chat-main">
            <Channel channel={activeChannel}>
              <Window>
                <CustomChannelHeader />
                <MessageList />
                <MessageInput />
              </Window>

              <Thread />
            </Channel>
          </div>
        </div>

        {isCreateModalOpen && (
          <CreateChannelModal onClose={() => setIsCreateModalOpen(false)} />
        )}
      </Chat>
    </div>
  );
};

export default HomePage;
