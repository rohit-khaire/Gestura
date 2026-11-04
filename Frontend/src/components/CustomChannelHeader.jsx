import {
  HashIcon,
  LockIcon,
  UsersIcon,
  PinIcon,
  VideoIcon,
} from "lucide-react";
import { useChannelStateContext, useChatContext } from "stream-chat-react";
import { useState } from "react";
import MembersModal from "./MembersModal";
import PinnedMessageModal from "./PinnedMessageModal";
import InviteModal from "./InviteModal";

const CustomChannelHeader = () => {
  const { channel } = useChannelStateContext();
  const { client } = useChatContext();
  const userId = client.userID;

  const memberCount = Object.keys(channel.state.members).length;

  const [showInvite, setShowInvite] = useState(false);
  const [showPinnedMessage, setShowPinnedMessage] = useState(false);
  const [pinnedMessage, setPinnedMessage] = useState([]);
  const [showMembers, setShowMembers] = useState(false);

  const isDM =
    channel.data?.member_count === 2 && channel.data?.id.includes("user_");
  const otherUser = Object.values(channel.state.members).find(
    (member) => member.user.id !== userId,
  );

  const handleShowPinned = async () => {
    const channelState = await channel.query();
    setPinnedMessage(channelState.pinned_messages);
    setShowPinnedMessage(true);
  };

  const handleVideoCall = async () => {
    if (channel) {
      const videoUrl = `${window.location.origin}/call/${channel.id}`;
      await channel.sendMessage({
        text: `I have started video call. Join me here: ${videoUrl}`,
      });
    }
  };

  return (
    <div className="h-14 border-b border-gray-200 flex items-center px-4 justify-between bg-white">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          {channel.data?.private ? (
            <LockIcon className="size-4 text-[#616061]" />
          ) : (
            <HashIcon className="size-4 text-[#616061]" />
          )}

          {isDM && otherUser?.user?.image && (
            <img
              src={otherUser.user.image}
              alt={otherUser.user.name || otherUser.user.id}
              className="size-7 rounded-full object-cover mr-1"
            />
          )}

          <span className="font-medium text-[#1D1C1D]">
            {isDM
              ? otherUser?.user?.name || otherUser?.user?.id
              : channel.data?.id}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4 ">
        <button
          className="flex items-center gap-2 hover:bg-[#F8F8F8] py-1 px-2 rounded cursor-pointer"
          onClick={() => setShowMembers(true)}
        >
          <UsersIcon className="size-5 text-[#616061]" />
          <span className="text-sm text-[#616061]">{memberCount}</span>
        </button>

        <button
          className="hover:bg-[#F8F8F8] p-1 rounded cursor-pointer"
          onClick={handleVideoCall}
          title="Start Video Call"
        >
          <VideoIcon className="size-5 text-[#1264A3]" />
        </button>

        {channel.data?.private && (
          <button
            className="btn btn-primary cursor-pointer"
            onClick={() => setShowInvite(true)}
          >
            Invite
          </button>
        )}

        <button
          className="hover:bg-[#F8F8F8] p-1 rounded cursor-pointer"
          onClick={handleShowPinned}
        >
          <PinIcon className="size-4 text-[#616061]" />
        </button>
      </div>

      {showMembers && (
        <MembersModal
          members={Object.values(channel.state.members)}
          onClose={() => setShowMembers(false)}
        />
      )}

      {showPinnedMessage && (
        <PinnedMessageModal
          pinnedMessages={pinnedMessage}
          onClose={() => setShowPinnedMessage(false)}
        />
      )}

      {showInvite && (
        <InviteModal channel={channel} onClose={() => setShowInvite(false)} />
      )}
    </div>
  );
};

export default CustomChannelHeader;
