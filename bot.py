import os
import discord
import mysql.connector

DISCORD_TOKEN='NOPE'
active_channels = ['secret-test', 'randomizer']
positive_emojis = ['👍', '😀', '👏']
negative_emojis = ['💩']
client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not isinstance(message.channel, discord.channel.DMChannel):
        if message.channel.name not in active_channels:
            return
    mydb = mysql.connector.connect(
        host="NOPE",
        user="NOPE",
        password="NOPE",
        database="NOPE")
    cursor = mydb.cursor()
    user_args = [message.author.id, message.author.name, message.author.display_name]
    cursor.callproc('insert_new_user_if_not_exists', user_args)
    mydb.commit()
    command_args = []
    include_unreleased = 0
    command_split = message.content.lower().split(' ', 1)
    if len(command_split) == 2:
        command_args = command_split[1].split()
        if 'unreleased' in command_args:
            include_unreleased = 1
    if command_split[0] == 'random':
        cursor.callproc('generate_list_name', [])
        for result in cursor.stored_results():
            the_result = result.fetchall()
            list_name = the_result[0]  
        return_embed = discord.Embed(title=f"New List: {list_name[0]}", color=0x93c47d)
        return_embed.set_footer(text=f"Crafted for {message.author.display_name}")
        if len(command_args) > 0:
            return_embed.add_field(name=f"Parameters", value=str(command_args), inline=False)
        primaries = []
        used_sec_id = 0
        used_sup_id = 0
        used_sec_persona = None
        collection_user = None
        if 'collection' in command_args:
            collection_user = message.author.id
        cursor.callproc('get_two_primaries', [ include_unreleased, collection_user ])
        for result in cursor.stored_results():
            pairs = result.fetchall()
            for primary in pairs:
                primaries.append(primary)
        primaries.sort(key=lambda x: x[2], reverse=True)
        for primary in sorted(primaries):
            if used_sup_id == 0:
                args = [primary[2], include_unreleased, primaries[0][3], primaries[1][3], collection_user, primary[4]]
                cursor.callproc('get_all_unit_combos', args)
                for result in cursor.stored_results():
                    squad = result.fetchall()
                    for dude in squad:
                        used_sec_id = dude[5]
                        used_sec_persona = dude[8]
                        used_sup_id = dude[6]
                        return_embed.add_field(name=f"Squad 1 ({str(primary[2])} SP)", value=f"Primary: {primary[0]}\n    Secondary: {dude[0]} ({str(dude[3])} pts)\n    Supporting: {dude[1]} ({str(dude[2])} pts)", inline=False)
            else:
                args = [primary[2], used_sec_id, used_sup_id, include_unreleased, primaries[0][3], primaries[1][3],  used_sec_persona, collection_user, primary[4]]
                cursor.callproc('get_second_squad', args)
                for result in cursor.stored_results():
                    squad = result.fetchall()
                    for dude in squad:
                        return_embed.add_field(name=f"Squad 2 ({str(primary[2])} SP)", value=f"Primary: {primary[0]}\n    Secondary: {dude[0]} ({str(dude[3])} pts)\n    Supporting: {dude[1]} ({str(dude[2])} pts)", inline=False)
        cursor.close()
        mydb.close()
    elif command_split[0] == 'collection':
        if message.content.lower().lstrip("collection ").startswith("add"):
            product = message.content.lower().lstrip("collection add ")
            the_result = 0
            add_collection_args = [message.author.id, product, the_result]
            result_args = cursor.callproc('add_group_to_collection', add_collection_args)
            mydb.commit()
            if result_args[2] == 0:
                response = f"That's not a valid product!"
            elif result_args[2] == 1:
                response = f"Successfully added {product} to your collection, {message.author.mention}."
            else:
                response = f"You already own {product}."
        elif message.content.lower().lstrip("collection ").startswith("view"):
            response = f"{message.author.mention}, your collection contains:"
            cursor.callproc('get_user_collection', [message.author.id])
            for result in cursor.stored_results():
                    all_results = result.fetchall()
                    for product in all_results:
                        product_id = product[0]
                        product_name = product[1]
                        response += '\n' + product_id + ': ' + product_name
        elif message.content.lower().lstrip("collection ").startswith("delete"):
            response = f"{message.author.mention}, your collection has been reset!"
            cursor.callproc('delete_user_collection', [message.author.id])
            mydb.commit()
        elif message.content.lower().lstrip("collection ").startswith("remove"):
            product = message.content.lower().lstrip("collection remove ")
            response = f"Removed {product} from your collection, {message.author.mention}"
            cursor.callproc('collection_remove', [message.author.id, product])
            mydb.commit()
        else:
            response = f"Invalid command for collection"
        cursor.close()
        mydb.close()
    elif command_split[0] == 'products':
        response = f"{message.author.mention}, here are the current available products:"
        cursor.callproc('get_all_products', [include_unreleased])
        prev_product_id = 'XXX'
        for result in cursor.stored_results():
            all_results = result.fetchall()
            for product in all_results:
                embed_string = ''
                product_id = product[0]
                product_name = product[1]
                if product[3] == False:
                    product_name += ' (Unreleased)'
                unit_name = product[2]
                if product_id != prev_product_id:
                    response += '\n' + product_id + ': ' + product_name
                if 'details' in command_args and unit_name:
                    response += '\n    -' + unit_name
                prev_product_id = product_id
        cursor.close()
        mydb.close()
    elif command_split[0] == 'help':
        response = 'Available commands:\n    random: this generates a random list. Optional parameters:'
        response += '\n        collection: only use units in your collection'
        response += '\n        unreleased: include units that aren''t yet for sale\n---------------------'
        response += '\n    collection: this allows you to track your Shatterpoint collection. Parameters:'
        response += '\n        add X: adds product X to your collection (use SWP-style code from "products" command)'
        response += '\n        remove X: removes product X from your collection'
        response += '\n        delete: this nukes your whole collection. Un-reversible. Tread lightly.'
        response += '\n        view: shows your current collection\n---------------------'
        response += '\n    products: this will display Shatterpoint products.'
    else:
        return
    if 'secret' in command_args:
        if command_split[0] == 'random':
            await message.author.send(embed=return_embed)
        else:
            await message.author.send(response)
    else:
        if command_split[0] == 'random':
            await message.reply(embed=return_embed)
        else:
            await message.channel.send(response)
    return

@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.author != client.user or reaction.message.channel.name not in active_channels or user == client.user:
        return
    if not reaction.message.embeds:
        return
    if reaction.emoji in positive_emojis:
        await reaction.message.channel.send(f"Glad you like the list, {user.mention}!")
    elif reaction.emoji in negative_emojis:
        await reaction.message.channel.send(f"Dang, {user.mention}, you try making a random list then!")
    return
client.run(DISCORD_TOKEN)
