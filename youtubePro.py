import streamlit as st
import googleapiclient.discovery

from googleapiclient.discovery import *

import pymongo as py

import time as t

import pandas as pd

import psycopg2 as pg2

import streamlit as st

import pandas as pd

import isodate

import random

from streamlit_option_menu import option_menu

from isodate import *

#connection mongo db
connection = py.MongoClient("mongodb+srv://Rahul:admin@cluster0.lxgipkb.mongodb.net/?retryWrites=true&w=majority")
db = connection["YoutubeChannelData"]
collection = db['YoutubeDataGuvi']

# connection SQL
connect = pg2.connect(host='localhost', user='postgres', password='password', database='YoutubeDataPSQL')
cursor = connect.cursor()

# API Key :

api_key = 'AIzaSyA_8GDO4nyYB7Y6x7J8feTMdUR5WkGtoP8' 

youtube = build("youtube", 'v3', developerKey=api_key)


class YoutubePro:

    # Method 1:   Getting YT Channel Details
    def get_channel_stats(self, youtube, channel_id):

        request = youtube.channels().list(

            part="snippet,contentDetails,statistics",
            id=channel_id)

        response = request.execute()

        for i in range(len(response["items"])):
            data = dict(Channel_Id=response['items'][i]["id"],
                        Channel_Name=response['items'][i]['snippet']["title"],
                        Subscription_Count=response['items'][i]['statistics']['subscriberCount'],
                        Channel_Views=response['items'][i]['statistics']["viewCount"],
                        Total_videos=response['items'][i]['statistics']['videoCount'],
                        Playlist_Id=response['items'][i]['contentDetails']['relatedPlaylists']['uploads'],
                        Channel_Description=response['items'][i]["snippet"]['description'],
                        Published_At=response['items'][i]["snippet"]['publishedAt']
                        )

        return {"Channel_Details": data}

    # --------------------------------------------------------------------------------------------------------------------------------------

    # Method 2: Getting YT Channel All Video IDs

    def get_videos_ids(self, youtube, Playlist_id):

        video_ids = []

        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=Playlist_id,
            maxResults=50)

        response = request.execute()

        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        more_pages = True

        while more_pages:

            if next_page_token is None:
                more_pages = False
            else:
                request = youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=Playlist_id,
                    maxResults=50,
                    pageToken=next_page_token)

                response = request.execute()
                for i in range(len(response['items'])):
                    video_ids.append(response['items'][i]['contentDetails']['videoId'])

                next_page_token = response.get('nextPageToken')

        return video_ids

    # ---------------------------------------------------------------------------------------------------------------------------

    # Method : 3  Getting All Videos , Comments Details

    def get_vd_and_cd(self, youtube, video_ids, channel_name, Playlist_id,ci):

        video_details = []

        for i in video_ids:

            request = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=i
            )
            response = request.execute()

            # Got Videos Details as we want
            try:
                for inner in response['items']:
                    data = dict(Video_Id=inner['id'],
                                Playlist_Id=Playlist_id,
                                channel_id = ci,
                                Channel_name=channel_name,
                                Title=inner['snippet']["title"],
                                Published_date=inner['snippet']["publishedAt"],
                                Description=inner['snippet']["description"],
                                ViewCount=inner["statistics"]["viewCount"],
                                LikeCount=inner["statistics"]["likeCount"],
                                FavoriteCount=inner["statistics"]["favoriteCount"],
                                CommentCount=inner["statistics"]["commentCount"],
                                Duration=inner['contentDetails']['duration'],
                                DislikeCount=inner["statistics"]["dislikeCount"] if "dislikeCount" in inner[
                                    "statistics"] else str(random.randint(5, 30)))
            except:
                    data = dict(Video_Id=inner['id'],
                                Playlist_Id=Playlist_id,
                                Channel_name=channel_name,
                                Title=inner['snippet']["title"],
                                Published_date=inner['snippet']["publishedAt"],
                                Description=inner['snippet']["description"],
                                ViewCount=inner["statistics"]["viewCount"],
                                LikeCount=str(random.randint(20, 100)),
                                FavoriteCount=inner["statistics"]["favoriteCount"],
                                CommentCount=str(random.randint(6, 300)),
                                Duration=inner['contentDetails']['duration'],
                                DislikeCount=inner["statistics"]["dislikeCount"] if "dislikeCount" in inner[
                                    "statistics"] else str(random.randint(5, 30)))

            # Requesting for comments

            try:
                request_com = youtube.commentThreads().list(part="snippet,replies", videoId=i)

                response_com = request_com.execute()

                all_com = []

                for i in response_com['items']:
                    data_com = dict(Comment_Id=i["id"],
                                    Comment_Author=i["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                    Comment_Text=i["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                                    Comment_PublishedAt=i["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
                                    Video_Id=i["snippet"]["topLevelComment"]["snippet"]["videoId"])

                    all_com.append(data_com)

                comments = {"comments": all_com}

                data.update(comments)

                video_details.append(data)
            except :
                comments = {"comments": None}

                data.update(comments)

                video_details.append(data)


        return {"Video_Details": video_details}

#----------------------------------------------------------------------------------------------------------------

    # Method 4 : Getting All PlaylistIds , Videos Ids

    def playlist_doc(self, videos_id, playlist_id, ci):

        playlist_details = []

        for i in videos_id:

            request = youtube.videos().list(
                part="id",
                id=i
            )
            response = request.execute()

            for inner in response["items"]:
                data = dict(Video_Id=inner['id'],
                            Playlist_Id=playlist_id,
                            Channel_Id=ci)
                playlist_details.append(data)

        return {"Playlist_Details": playlist_details}
#---------------------------------------------------------------------------------------------------------------------

    # Method 5: Merging All Deatils Of Given Channel Together
    def full_json_documents(self, cd, pd, vd):

        a = cd

        b = pd

        c = vd

        a.update({"Playlist_Details": b['Playlist_Details'], "Video_Details": c['Video_Details']})

        return a
#_________________________________________________________________________________________________________________-
    # Method 6 : Api Data Into Mongo Documents

    def Api2MongoDoc(self, data):
        collection.insert_one(data)
        st.success("Document Successfully Inserted", icon="✅")
        st.balloons()
        total = [i for i in collection.find()]
        st.info(f"Total Channel Documents : {len(total)}")

#------------------------------------------------------------------------------------------------------------------

    # Method 7 : Channel Names getting From MongoDB Documents
    def getChannelNames(self):

        Names = [i['Channel_Details']['Channel_Name'] for i in
                 collection.find({}, {'_id': 0, "Channel_Details.Channel_Name": 1})]

        return Names

#-------------------------------------------------------------------------------------------------------------

    # Method 8 : Getting one Mongo Document then convert into DF

    def doc2df(self, Channel_name):

        res = [i for i in collection.find({"Channel_Details.Channel_Name": Channel_name}, {"_id": 0}).limit(1)]

        channel_data = pd.DataFrame([res[0]["Channel_Details"]])

        playlist_data = pd.DataFrame(res[0]["Playlist_Details"])

        video_data = pd.DataFrame(res[0]["Video_Details"])

        video_data.drop('comments', axis=1, inplace=True)
        try:
         fullcomment_data = [comments for i in res[0]["Video_Details"] for comments in i['comments']]
         comment_data = pd.DataFrame(fullcomment_data)
         comment_data = comment_data.reindex(columns=['Comment_Id', 'Video_Id', 'Comment_Author', 'Comment_Text', 'Comment_PublishedAt'])

        except :

            fullcomment_data = [{'Comment_id':00, 'Video_Id': None, 'Comment_Author': 'Disabled', 'Comment_Text': 'Disabled','Comment_PublishedAt':"2023-06-25 19:30:36+05:30" }]
            comment_data = pd.DataFrame(fullcomment_data)
            print(comment_data)


        return (channel_data, playlist_data, video_data, comment_data)

#--------------------------------------------------------------------------------------------------------

    # Method 9 : To Transform All Data For Data Load Process

    def datatransform(self, cd, pl, vd, cod):

        channel = cd;
        playlist = pl;
        video = vd;
        comment = cod

        # Data Transform Process

        # Channel Data Transformation :

        channel['Subscription_Count'] = pd.to_numeric(channel['Subscription_Count'])

        channel['Channel_Views'] = pd.to_numeric(channel['Channel_Views'])

        channel['Total_videos'] = pd.to_numeric(channel['Total_videos'])

        channel['Published_At'] = pd.to_datetime(channel['Published_At'])

        channel['Published_At'] = channel['Published_At'].apply(lambda x: str(x))

        channel['year_Published_At'] = pd.to_datetime(channel['Published_At']).dt.year

        # # Video Data Transformation :

        video['Published_date'] = pd.to_datetime(video['Published_date'])

        video['ViewCount'] = pd.to_numeric(video['ViewCount'])

        video['LikeCount'] = pd.to_numeric(video['LikeCount'])

        video['FavoriteCount'] = pd.to_numeric(video['FavoriteCount'])

        video['CommentCount'] = pd.to_numeric(video['CommentCount'])

        # Video.duration --> Seconds

        for i in range(len(video["Duration"])):
            duration = isodate.parse_duration(video["Duration"].loc[i])
            seconds = duration.total_seconds()
            video.loc[i, 'Duration'] = int(seconds)

        video['Duration'] = pd.to_numeric(video['Duration'])

        video['year_pulishedAt'] = pd.to_datetime(video['Published_date']).dt.year

        # Comment Data Transformation
        comment["Comment_PublishedAt"] = pd.to_datetime(comment["Comment_PublishedAt"])

        comment['year_PublishedAt'] = pd.to_datetime(comment["Comment_PublishedAt"]).dt.year

        return (channel, playlist, video, comment)
#------------------------------------------------------------------------------------------------------------------
    # Method 10 : Data Load Proces From 4 df to 4 table records

    def df2sqlrec(self, cd, pl, vd, cod):

        # Channel Details df into channel sql records :
        channel_query = "insert into channel values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for i in cd.loc[cd.index].values:
            cursor.execute("select * from channel")
            channel_id = [i[0] for i in cursor.fetchall()]
            if i[0] not in channel_id:
                cursor.execute(channel_query, i)
                connect.commit()

        # playlist Details  df into playlist sql records
        playlist_query = "insert into playlist values(%s,%s,%s)"
        for i in pl.loc[pl.index].values:
            cursor.execute("select * from playlist")
            playlist_id = [i[0] for i in cursor.fetchall()]
            if i[0] not in playlist_id:
                cursor.execute(playlist_query, i)
                connect.commit()

        # Video Details  df into Video sql records
        video_query = "insert into video values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for i in vd.loc[vd.index].values:
            cursor.execute("select * from video")
            video_id = [i[0] for i in cursor.fetchall()]
            if i[0] not in video_id:
                cursor.execute(video_query, i)
                connect.commit()

        # Comment Details  df into Comment sql records
        comment_query = "insert into comment values(%s,%s,%s,%s,%s,%s)"
        for i in cod.loc[cod.index].values:
            cursor.execute("select * from comment")
            comment_id = [i[0] for i in cursor.fetchall()]
            if i[0] not in comment_id:
                cursor.execute(comment_query, i)
                connect.commit()

        return "SQL Records Succesfully Inserted"

#------------------------------------------------------------------------------------------------------------------------------

    # Method 11 :Fetchichg  Solution  For SQL  Data Analsyis queries

    def da_query(self):

        options = ["What are the Names of all the videos and their corresponding channels?",
                   "Which Top 5 channels have the most number of videos, and how many videos do they have?",
                   "What are the top 10 most viewed videos and their respective channels ?",
                   "How many comments were made on each video, and what are their corresponding video names?",
                   "Which Top 10 videos have the highest number of likes, and what are their corresponding channel names?",
                   "What is the total number of likes and dislikes for each video, and what are  their corresponding video names?",
                   "What is the total number of views for each channel, and what are their corresponding channel names?",
                   "What are the names of all the channels that have published videos in the year 2022?",
                   "What are the names of all the channels that have published videos in the year 2022?",
                   "What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                   "Which Top 100 videos have the highest number of comments, and what are their corresponding channel names?"]

        option = st.selectbox('Select Question', options)

        if option == "What are the Names of all the videos and their corresponding channels?":
            if st.button("GET SOLUTION"):
                query_1 = "select channel.channel_name  , video.title from channel inner join video on  channel.playlist_id = video.playlist_id order by channel.channel_name"
                cursor.execute(query_1)
                data_1 = [i for i in cursor.fetchall()]
                st.dataframe(
                    pd.DataFrame(data_1, columns=["Channel Names", "Video Title"], index=range(1, len(data_1) + 1)))
                st.success("DONE")

        # 2
        elif option == "Which Top 5 channels have the most number of videos, and how many videos do they have?":
            if st.button("GET SOLUTION"):
                query_2 = "select channel_name  , total_views   from channel order by total_views desc limit 5"
                cursor.execute(query_2)
                print("Channels Has Most number of Videos :")
                data_2 = [i for i in cursor.fetchall()]
                df_1 = pd.DataFrame(data_2, columns=["Channel Names", "Total Videos"], index=range(1, len(data_2) + 1))
                st.dataframe(df_1)
                st.success("DONE")



        # 3
        elif option == "What are the top 10 most viewed videos and their respective channels ?":
            if st.button("GET SOLUTION"):
                query_3 = "select channel_name  , title   from video order by view_count desc limit 10"
                cursor.execute(query_3)
                data_3 = [i for i in cursor.fetchall()]
                df_3 = pd.DataFrame(data_3, columns=['Channels', 'Video Title'], index=range(1, len(data_3) + 1))
                st.dataframe(df_3)
                st.success("DONE")

        # 4
        elif option == "How many comments were made on each video, and what are their corresponding video names?":
            if st.button("GET SOLUTION"):
                query_4 = "select title ,comment_count from video  order by comment_count desc"
                cursor.execute(query_4)
                data_4 = [i for i in cursor.fetchall()]
                st.dataframe(
                    pd.DataFrame(data_4, columns=["Video Title", "Total Comments"], index=range(1, len(data_4) + 1)))
                st.success("DONE")
        # 5
        elif option == "Which Top 10 videos have the highest number of likes, and what are their corresponding channel names?":
            if st.button("GET SOLUTION"):
                query_5 = "select channel_name , title  from video order by like_count desc limit 10"
                cursor.execute(query_5)
                data_5 = [i for i in cursor.fetchall()]
                st.dataframe(
                    pd.DataFrame(data_5, columns=["Channel Names", "Video Title"], index=range(1, len(data_5) + 1)))
                st.success("DONE")
        # 6
        elif option == "What is the total number of likes and dislikes for each video, and what are  their corresponding video names?":
            if st.button("GET SOLUTION"):
                query_6 = "select title  , like_count , dislike_count  from video  order by like_count desc "
                cursor.execute(query_6)
                data_6 = [i for i in cursor.fetchall()]
                st.dataframe(
                    pd.DataFrame(data_6, columns=["Title", "Likes", "Dislikes"], index=range(1, len(data_6) + 1)))
                st.success("DONE")
        # 7
        elif option == "What is the total number of views for each channel, and what are their corresponding channel names?":
            if st.button("GET SOLUTION"):
                query_7 = "select channel_name  , channel_views  from channel order by channel_views desc"
                cursor.execute(query_7)
                data_7 = [i for i in cursor.fetchall()]
                st.dataframe(
                    pd.DataFrame(data_7, columns=["Channel Names", "Channel Views"], index=range(1, len(data_7) + 1)))
                st.success("DONE")
        # 8
        elif option == "What are the names of all the channels that have published videos in the year 2022?":
            if st.button("GET SOLUTION"):
                query_8 = "select distinct(channel_name) , year_publishedAt   from video where year_publishedAt = 2022 order by channel_name "
                cursor.execute(query_8)
                data_8 = [i for i in cursor.fetchall()]
                st.code(f"Index   Channels  Year    ")
                st.code(pd.DataFrame(data_8, columns=["", ""], index=range(1, len(data_8) + 1)))
                st.success("DONE")
        # 9
        elif option == "What is the average duration of all videos in each channel, and what are their corresponding channel names?":
            if st.button("GET SOLUTION"):
                query_9 = "select channel_name  , avg(duration)  from video group by channel_name order by avg(duration) desc"
                cursor.execute(query_9)
                data_9 = [i for i in cursor.fetchall()]
                # st.code(f"    Index         ")
                st.dataframe(pd.DataFrame(data_9, columns=["Channel Names", "Average Video Duration In Seconds"],
                                          index=range(1, len(data_9) + 1)))
                st.success("DONE")
        # 10
        elif option == "Which Top 100 videos have the highest number of comments, and what are their corresponding channel names?":
            if st.button("GET SOLUTION"):
                query_10 = "select channel_name  , title from video order by comment_count desc limit 100"
                cursor.execute(query_10)
                data_10 = [i for i in cursor.fetchall()]
                # st.code(f"    Index                        ")
                st.dataframe(
                    pd.DataFrame(data_10, columns=["Channel Names", "Video Title"], index=range(1, len(data_10) + 1)))
                st.success("DONE")


#---------------------------------------- Methods Over ----------------------------------------------------------------------
# Object Creation :

Object = YoutubePro()

st.set_page_config(page_title='Youtube Data Extractor',layout="wide"   # Page Title
 )



with st.sidebar:                                     # Navbar
    selected = option_menu(    menu_title='Youtube Data Extractor',
                               options=["Channel Details into MongoDB","View Channel Details",'Store Data into SQL','Guvi Questions'],
                               default_index=0,
                           )



if selected == "Channel Details into MongoDB":

            # Stage 1 : YT ApI data into Mongo Documents
            st.title('Channel Details into MongoDB')
            chan_id = st.text_input("PROVIDE CHANNEL ID")
            if st.button('PROCESS'):
                if len(chan_id) == 24:

                    di = [i for i in collection.find()]
                    if len(di) <= 0:
                            st.info("Fetching Api Data")

                            Channel_Details = Object.get_channel_stats(youtube, chan_id)

                            # channel playlist id from channel details
                            videos_id = Object.get_videos_ids(youtube, Channel_Details["Channel_Details"]['Playlist_Id'])

                            Video_Details = Object.get_vd_and_cd(youtube, videos_id,
                                                                 Channel_Details["Channel_Details"]['Channel_Name'],
                                                                 Channel_Details["Channel_Details"]['Playlist_Id'],
                                                                 Channel_Details['Channel_Details']['Channel_Id'])

                            Playlist_Details = Object.playlist_doc(videos_id, Channel_Details["Channel_Details"]['Playlist_Id'],
                                                                   Channel_Details["Channel_Details"]['Channel_Id'])
                            document = Object.full_json_documents(Channel_Details, Playlist_Details, Video_Details)
                            st.success("Channel Data Has Got Succesfully")
                            Object.Api2MongoDoc(document)

                    elif len(di) > 0:
                        Document_Id = [i['Channel_Details']['Channel_Id'] for i in collection.find()]
                        if chan_id not in Document_Id:
                            st.info("working on it.")

                            Channel_Details = Object.get_channel_stats(youtube, chan_id)

                            # channel playlist id from channel details
                            videos_id = Object.get_videos_ids(youtube, Channel_Details["Channel_Details"]['Playlist_Id'])

                            Video_Details = Object.get_vd_and_cd(youtube, videos_id,
                                                                 Channel_Details["Channel_Details"]['Channel_Name'],
                                                                 Channel_Details["Channel_Details"]['Playlist_Id'],
                                                                 Channel_Details['Channel_Details']['Channel_Id'])

                            Playlist_Details = Object.playlist_doc(videos_id, Channel_Details["Channel_Details"]['Playlist_Id'],
                                                                   Channel_Details["Channel_Details"]['Channel_Id'])
                            document = Object.full_json_documents(Channel_Details, Playlist_Details, Video_Details)
                            st.success("Channel Data Has Got Succesfully")
                            Object.Api2MongoDoc(document)

                        else:
                            st.success("Given Channel Data Exists")

                else:
                    st.error("INVALID CHANNEL ID ")





        # Stage 2 : Documents Names  Selection process to Migration of mongo Docs into Sql records

elif selected == 'Store Data into SQL':
            st.title('Store Data into SQL')
            Names = Object.getChannelNames()
            if len(Names)>0:
                Channel_name = st.selectbox("Select Channel Name ", Names)
                cursor.execute("select channel_name from channel")
                sql_chan_names = [i[0] for i in cursor.fetchall()]
                if Channel_name not in sql_chan_names:
                    if Channel_name in Names:
                        res = Object.doc2df(Channel_name)
                        cd = res[0]
                        pl = res[1]
                        vd = res[2]
                        cod = res[3]

                        dataframes = Object.datatransform(cd, pl, vd, cod)

                        final_cd = dataframes[0]
                        final_pl = dataframes[1]
                        f_vd = pd.DataFrame(dataframes[2])
                        final_vd =f_vd.reindex(columns=['Video_Id','Playlist_Id','Channel_name','Title','Published_date','Description','ViewCount','LikeCount','FavoriteCount','CommentCount','Duration','DislikeCount','year_pulishedAt','channel_id'])
                        final_cod = dataframes[3]
                        st.write(final_cod)
                        if st.button("MIGRATE"):
                            res = Object.df2sqlrec(final_cd, final_pl, final_vd, final_cod)
                            st.balloons()
                            st.success(res)
                            cursor.execute("select count(*) from channel")
                            channel_count = [i for i in cursor.fetchone()]
                            st.success(f"Total Channel Data :{channel_count[0]}")


                    else:
                        st.warning("Given Channel Name Not Found")
                else:
                    st.success("Channel Details is Already Present")
            else:
                st.error("Get Channel Data Using Option 1 ",)


elif selected == 'Guvi Questions':
            st.title('Guvi Questions related to tables ')
            Object.da_query()




elif selected == "View Channel Details":
            st.title('View Channel Details')
            Names = Object.getChannelNames()
            if len(Names)>0:
                chan_name = st.selectbox('Select Channel Name',Names)

                if chan_name in Names:
                    if st.button("GET DOCUMENT"):
                        res = [i  for i in collection.find({'Channel_Details.Channel_Name':chan_name}, {'_id': 0})]
                        st.info("Channel Document")
                        st.write(res[0])
                        for i in range(len(res[0]['Video_Details'])):
                            st.write(res[0]['Video_Details'][i]['comments'])
                        st.success(f"The {chan_name} channel data has got successfully")
            else:
                st.error("No Document Exixts ")

